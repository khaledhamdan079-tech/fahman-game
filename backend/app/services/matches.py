from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.models import (
    Category,
    LifelineState,
    LifelineType,
    Match,
    MatchCategory,
    MatchEvent,
    MatchLifeline,
    MatchQuestion,
    MatchQuestionState,
    MatchStatus,
    MatchTeam,
    Question,
    QuestionOption,
    QuestionStatus,
    QuestionType,
    User,
    UserQuestionUsage,
)
from app.schemas.matches import (
    ActiveQuestion,
    BoardQuestion,
    LifelineView,
    MatchCategoryView,
    MatchCreateRequest,
    MatchHistoryResponse,
    MatchStateResponse,
    MatchSummary,
    TeamState,
)
from app.services.categories import active_reservations_for_user


def now_utc() -> datetime:
    return datetime.now(UTC)


def command_error(
    code: str, message: str, *, status_code: int = 409, **details: object
) -> AppError:
    return AppError(code, message, status_code=status_code, details=details or None)


async def _owned_match(
    session: AsyncSession, match_id: UUID, user_id: UUID, *, lock: bool = False
) -> Match:
    statement = select(Match).where(Match.id == match_id, Match.owner_id == user_id)
    if lock:
        statement = statement.with_for_update()
    match = await session.scalar(statement)
    if match is None:
        raise AppError("MATCH_NOT_FOUND", "Match not found", status_code=404)
    return match


async def _begin_command(
    session: AsyncSession,
    match_id: UUID,
    user_id: UUID,
    expected_version: int,
    idempotency_key: str,
    event_type: str,
) -> tuple[Match, bool]:
    match = await _owned_match(session, match_id, user_id, lock=True)
    prior = await session.scalar(
        select(MatchEvent).where(
            MatchEvent.match_id == match.id,
            MatchEvent.idempotency_key == idempotency_key,
        )
    )
    if prior is not None:
        if prior.event_type != event_type:
            raise command_error(
                "IDEMPOTENCY_CONFLICT",
                "This idempotency key was used for another command",
                current_version=match.version,
            )
        return match, True
    if match.version != expected_version:
        raise command_error(
            "STALE_MATCH_VERSION",
            "The match changed; refresh before trying again",
            current_version=match.version,
        )
    if match.status != MatchStatus.ACTIVE:
        raise command_error("MATCH_NOT_ACTIVE", "The match is not active")
    return match, False


def _record_event(
    session: AsyncSession,
    match: Match,
    user_id: UUID,
    idempotency_key: str,
    event_type: str,
    payload: dict[str, object],
) -> None:
    match.version += 1
    session.add(
        MatchEvent(
            match_id=match.id,
            sequence_no=match.version,
            event_type=event_type,
            actor_user_id=user_id,
            idempotency_key=idempotency_key,
            payload=payload,
        )
    )


async def create_match(
    session: AsyncSession,
    user: User,
    request: MatchCreateRequest,
    idempotency_key: str,
) -> MatchStateResponse:
    existing = await session.scalar(
        select(Match)
        .join(MatchEvent, MatchEvent.match_id == Match.id)
        .where(
            Match.owner_id == user.id,
            MatchEvent.idempotency_key == idempotency_key,
            MatchEvent.event_type == "match_created",
        )
    )
    if existing is not None:
        return await get_match_state(session, existing.id, user.id)

    categories = (
        await session.scalars(
            select(Category)
            .where(Category.id.in_(request.category_ids), Category.is_active.is_(True))
            .with_for_update()
        )
    ).all()
    by_id = {category.id: category for category in categories}
    if len(by_id) != len(request.category_ids):
        raise command_error("CATEGORY_NOT_ELIGIBLE", "One or more categories are unavailable")

    reserved = active_reservations_for_user(user.id)
    selections: list[tuple[int, int, Question]] = []
    for category_position, category_id in enumerate(request.category_ids):
        for tier_position, points in enumerate((200, 400, 600)):
            used = select(UserQuestionUsage.question_id).where(UserQuestionUsage.user_id == user.id)
            questions = (
                await session.scalars(
                    select(Question)
                    .where(
                        Question.category_id == category_id,
                        Question.points == points,
                        Question.status == QuestionStatus.PUBLISHED,
                        Question.id.not_in(used),
                        Question.id.not_in(reserved),
                    )
                    .order_by(func.random())
                    .limit(2)
                    .with_for_update(skip_locked=True)
                )
            ).all()
            if len(questions) != 2:
                raise command_error(
                    "CATEGORY_NOT_ELIGIBLE",
                    "A selected category no longer has enough unused questions",
                    category_id=str(category_id),
                    points=points,
                )
            for offset, question in enumerate(questions):
                selections.append((category_position, tier_position * 2 + offset, question))

    question_ids = [question.id for _, _, question in selections]
    option_rows = (
        await session.scalars(
            select(QuestionOption)
            .where(QuestionOption.question_id.in_(question_ids))
            .order_by(QuestionOption.question_id, QuestionOption.sort_order)
        )
    ).all()
    options: dict[UUID, list[dict[str, object]]] = {question_id: [] for question_id in question_ids}
    for option in option_rows:
        options[option.question_id].append(
            {
                "text_ar": option.text_ar,
                "sort_order": option.sort_order,
                "is_correct": option.is_correct,
            }
        )

    created_at = now_utc()
    match = Match(
        owner_id=user.id,
        status=MatchStatus.ACTIVE,
        current_team_no=1,
        timer_seconds=request.timer_seconds,
        version=1,
        started_at=created_at,
    )
    session.add(match)
    await session.flush()
    session.add_all(
        [
            MatchTeam(match_id=match.id, team_no=1, name=request.team_one_name),
            MatchTeam(match_id=match.id, team_no=2, name=request.team_two_name),
        ]
    )
    session.add_all(
        [
            MatchCategory(match_id=match.id, category_id=category_id, position=position)
            for position, category_id in enumerate(request.category_ids)
        ]
    )
    for category_position, slot_position, question in selections:
        session.add(
            MatchQuestion(
                match_id=match.id,
                question_id=question.id,
                category_position=category_position,
                slot_position=slot_position,
                question_type_snapshot=question.question_type,
                prompt_snapshot=question.prompt_ar,
                answer_snapshot=question.answer_ar,
                options_snapshot=options[question.id],
                media_asset_id_snapshot=question.media_asset_id,
                points=question.points,
                max_plays=question.max_plays,
            )
        )
    session.add_all(
        [
            MatchLifeline(match_id=match.id, team_no=team_no, lifeline_type=lifeline_type)
            for team_no in (1, 2)
            for lifeline_type in LifelineType
        ]
    )
    session.add(
        MatchEvent(
            match_id=match.id,
            sequence_no=1,
            event_type="match_created",
            actor_user_id=user.id,
            idempotency_key=idempotency_key,
            payload={"category_ids": [str(item) for item in request.category_ids]},
        )
    )
    await session.commit()
    return await get_match_state(session, match.id, user.id)


async def get_match_state(
    session: AsyncSession, match_id: UUID, user_id: UUID
) -> MatchStateResponse:
    match = await _owned_match(session, match_id, user_id)
    teams = (
        await session.scalars(
            select(MatchTeam).where(MatchTeam.match_id == match.id).order_by(MatchTeam.team_no)
        )
    ).all()
    category_rows = (
        await session.execute(
            select(MatchCategory, Category)
            .join(Category, Category.id == MatchCategory.category_id)
            .where(MatchCategory.match_id == match.id)
            .order_by(MatchCategory.position)
        )
    ).all()
    questions = (
        await session.scalars(
            select(MatchQuestion)
            .where(MatchQuestion.match_id == match.id)
            .order_by(MatchQuestion.category_position, MatchQuestion.slot_position)
        )
    ).all()
    lifelines = (
        await session.scalars(
            select(MatchLifeline)
            .where(MatchLifeline.match_id == match.id)
            .order_by(MatchLifeline.team_no, MatchLifeline.lifeline_type)
        )
    ).all()
    by_position: dict[int, list[BoardQuestion]] = {row.position: [] for row, _ in category_rows}
    for question in questions:
        by_position[question.category_position].append(
            BoardQuestion(
                id=question.id,
                points=question.points,
                question_type=question.question_type_snapshot,
                state=question.state,
                play_count=question.play_count,
                max_plays=question.max_plays,
                choosing_team_no=question.choosing_team_no,
                answered_by_team_no=question.answered_by_team_no,
                awarded_points=question.awarded_points,
            )
        )

    active_model = next(
        (
            question
            for question in questions
            if question.state in (MatchQuestionState.OPEN, MatchQuestionState.REVEALED)
        ),
        None,
    )
    active: ActiveQuestion | None = None
    if active_model is not None:
        doubled = any(
            item.lifeline_type == LifelineType.DOUBLE_POINTS
            and item.match_question_id == active_model.id
            and item.state == LifelineState.USED
            for item in lifelines
        )
        safe_options = [
            {"text_ar": item["text_ar"], "sort_order": item["sort_order"]}
            for item in active_model.options_snapshot
        ]
        active = ActiveQuestion(
            id=active_model.id,
            question_type=active_model.question_type_snapshot,
            prompt_ar=active_model.prompt_snapshot,
            options=safe_options,
            answer_ar=(
                active_model.answer_snapshot
                if active_model.state == MatchQuestionState.REVEALED
                else None
            ),
            points=active_model.points,
            effective_points=active_model.points * (2 if doubled else 1),
            state=active_model.state,
            media_asset_id=active_model.media_asset_id_snapshot,
            media_ready_at=active_model.media_ready_at,
            deadline_at=active_model.deadline_at,
            play_count=active_model.play_count,
            max_plays=active_model.max_plays,
            choosing_team_no=active_model.choosing_team_no,
        )

    return MatchStateResponse(
        id=match.id,
        status=match.status,
        current_team_no=match.current_team_no,
        timer_seconds=match.timer_seconds,
        version=match.version,
        started_at=match.started_at,
        finished_at=match.finished_at,
        created_at=match.created_at,
        teams=[TeamState(team_no=item.team_no, name=item.name, score=item.score) for item in teams],
        categories=[
            MatchCategoryView(
                id=category.id,
                name_ar=category.name_ar,
                position=match_category.position,
                questions=by_position[match_category.position],
            )
            for match_category, category in category_rows
        ],
        lifelines=[
            LifelineView(
                team_no=item.team_no,
                lifeline_type=item.lifeline_type,
                state=item.state,
                match_question_id=item.match_question_id,
            )
            for item in lifelines
        ],
        active_question=active,
    )


async def get_active_match_state(session: AsyncSession, user_id: UUID) -> MatchStateResponse | None:
    match_id = await session.scalar(
        select(Match.id)
        .where(
            Match.owner_id == user_id,
            Match.status.in_((MatchStatus.SETUP, MatchStatus.ACTIVE)),
        )
        .order_by(Match.created_at.desc())
        .limit(1)
    )
    if match_id is None:
        return None
    return await get_match_state(session, match_id, user_id)


async def open_question(
    session: AsyncSession,
    match_id: UUID,
    question_id: UUID,
    user_id: UUID,
    expected_version: int,
    idempotency_key: str,
) -> MatchStateResponse:
    match, duplicate = await _begin_command(
        session, match_id, user_id, expected_version, idempotency_key, "question_opened"
    )
    if duplicate:
        return await get_match_state(session, match.id, user_id)
    active_count = await session.scalar(
        select(func.count(MatchQuestion.id)).where(
            MatchQuestion.match_id == match.id,
            MatchQuestion.state.in_((MatchQuestionState.OPEN, MatchQuestionState.REVEALED)),
        )
    )
    if active_count:
        raise command_error("QUESTION_ALREADY_ACTIVE", "Finish the active question first")
    question = await session.scalar(
        select(MatchQuestion)
        .where(MatchQuestion.id == question_id, MatchQuestion.match_id == match.id)
        .with_for_update()
    )
    if question is None or question.state not in (
        MatchQuestionState.AVAILABLE,
        MatchQuestionState.PREPARED,
    ):
        raise command_error("QUESTION_NOT_AVAILABLE", "This question is not available")
    armed_double = await session.scalar(
        select(MatchLifeline).where(
            MatchLifeline.match_id == match.id,
            MatchLifeline.team_no == match.current_team_no,
            MatchLifeline.lifeline_type == LifelineType.DOUBLE_POINTS,
            MatchLifeline.state == LifelineState.ARMED,
        )
    )
    if armed_double is not None and armed_double.match_question_id != question.id:
        raise command_error(
            "LIFELINE_TARGET_MISMATCH",
            "Open the question prepared for double points or cancel the lifeline",
        )
    timestamp = now_utc()
    question.state = MatchQuestionState.OPEN
    question.choosing_team_no = match.current_team_no
    question.opened_at = timestamp
    if question.question_type_snapshot == QuestionType.TEXT:
        question.deadline_at = timestamp + timedelta(seconds=match.timer_seconds)
    if armed_double is not None:
        armed_double.state = LifelineState.USED
        armed_double.used_at = timestamp
    usage = await session.get(UserQuestionUsage, (user_id, question.question_id))
    if usage is None:
        session.add(
            UserQuestionUsage(
                user_id=user_id,
                question_id=question.question_id,
                first_match_id=match.id,
                first_used_at=timestamp,
            )
        )
    _record_event(
        session,
        match,
        user_id,
        idempotency_key,
        "question_opened",
        {"match_question_id": str(question.id), "team_no": match.current_team_no},
    )
    await session.commit()
    return await get_match_state(session, match.id, user_id)


async def arm_lifeline(
    session: AsyncSession,
    match_id: UUID,
    lifeline_type: LifelineType,
    question_id: UUID,
    user_id: UUID,
    expected_version: int,
    idempotency_key: str,
) -> MatchStateResponse:
    event_type = f"lifeline_{lifeline_type.value}"
    match, duplicate = await _begin_command(
        session, match_id, user_id, expected_version, idempotency_key, event_type
    )
    if duplicate:
        return await get_match_state(session, match.id, user_id)
    question = await session.scalar(
        select(MatchQuestion)
        .where(MatchQuestion.id == question_id, MatchQuestion.match_id == match.id)
        .with_for_update()
    )
    if question is None:
        raise command_error("QUESTION_NOT_AVAILABLE", "This question is not available")
    lifeline = await session.scalar(
        select(MatchLifeline)
        .where(
            MatchLifeline.match_id == match.id,
            MatchLifeline.team_no == match.current_team_no,
            MatchLifeline.lifeline_type == lifeline_type,
        )
        .with_for_update()
    )
    if lifeline is None or lifeline.state != LifelineState.AVAILABLE:
        raise command_error("LIFELINE_ALREADY_USED", "This lifeline is no longer available")
    timestamp = now_utc()
    if lifeline_type == LifelineType.DOUBLE_POINTS:
        if question.state != MatchQuestionState.AVAILABLE:
            raise command_error(
                "LIFELINE_WRONG_TIMING", "Double points must be armed before opening"
            )
        question.state = MatchQuestionState.PREPARED
        lifeline.state = LifelineState.ARMED
    else:
        if (
            question.state != MatchQuestionState.OPEN
            or question.choosing_team_no != match.current_team_no
        ):
            raise command_error("LIFELINE_WRONG_TIMING", "Use this lifeline on your open question")
        lifeline.state = LifelineState.USED
        lifeline.used_at = timestamp
    lifeline.match_question_id = question.id
    _record_event(
        session,
        match,
        user_id,
        idempotency_key,
        event_type,
        {"match_question_id": str(question.id), "team_no": match.current_team_no},
    )
    await session.commit()
    return await get_match_state(session, match.id, user_id)


async def cancel_armed_lifeline(
    session: AsyncSession,
    match_id: UUID,
    lifeline_type: LifelineType,
    user_id: UUID,
    expected_version: int,
    idempotency_key: str,
) -> MatchStateResponse:
    event_type = f"lifeline_{lifeline_type.value}_cancelled"
    match, duplicate = await _begin_command(
        session, match_id, user_id, expected_version, idempotency_key, event_type
    )
    if duplicate:
        return await get_match_state(session, match.id, user_id)
    lifeline = await session.scalar(
        select(MatchLifeline)
        .where(
            MatchLifeline.match_id == match.id,
            MatchLifeline.team_no == match.current_team_no,
            MatchLifeline.lifeline_type == lifeline_type,
        )
        .with_for_update()
    )
    if lifeline is None or lifeline.state != LifelineState.ARMED:
        raise command_error("LIFELINE_NOT_ARMED", "This lifeline cannot be cancelled")
    if lifeline.match_question_id is not None:
        question = await session.get(MatchQuestion, lifeline.match_question_id)
        if question is not None and question.state == MatchQuestionState.PREPARED:
            question.state = MatchQuestionState.AVAILABLE
    previous_question_id = lifeline.match_question_id
    lifeline.state = LifelineState.AVAILABLE
    lifeline.match_question_id = None
    _record_event(
        session,
        match,
        user_id,
        idempotency_key,
        event_type,
        {"match_question_id": str(previous_question_id)},
    )
    await session.commit()
    return await get_match_state(session, match.id, user_id)


async def cancel_match(
    session: AsyncSession,
    match_id: UUID,
    user_id: UUID,
    expected_version: int,
    idempotency_key: str,
) -> MatchStateResponse:
    match, duplicate = await _begin_command(
        session, match_id, user_id, expected_version, idempotency_key, "match_cancelled"
    )
    if duplicate:
        return await get_match_state(session, match.id, user_id)
    match.status = MatchStatus.CANCELLED
    match.finished_at = now_utc()
    _record_event(session, match, user_id, idempotency_key, "match_cancelled", {})
    await session.commit()
    return await get_match_state(session, match.id, user_id)


async def mark_media_ready(
    session: AsyncSession,
    match_id: UUID,
    question_id: UUID,
    user_id: UUID,
    expected_version: int,
    idempotency_key: str,
) -> MatchStateResponse:
    match, duplicate = await _begin_command(
        session, match_id, user_id, expected_version, idempotency_key, "media_ready"
    )
    if duplicate:
        return await get_match_state(session, match.id, user_id)
    question = await session.scalar(
        select(MatchQuestion)
        .where(MatchQuestion.id == question_id, MatchQuestion.match_id == match.id)
        .with_for_update()
    )
    if (
        question is None
        or question.state != MatchQuestionState.OPEN
        or question.media_asset_id_snapshot is None
        or question.media_ready_at is not None
    ):
        raise command_error("INVALID_STATE_TRANSITION", "Media is not waiting to become ready")
    timestamp = now_utc()
    question.media_ready_at = timestamp
    question.deadline_at = timestamp + timedelta(seconds=match.timer_seconds)
    _record_event(
        session,
        match,
        user_id,
        idempotency_key,
        "media_ready",
        {"match_question_id": str(question.id)},
    )
    await session.commit()
    return await get_match_state(session, match.id, user_id)


async def record_media_play(
    session: AsyncSession,
    match_id: UUID,
    question_id: UUID,
    user_id: UUID,
    expected_version: int,
    idempotency_key: str,
) -> MatchStateResponse:
    match, duplicate = await _begin_command(
        session, match_id, user_id, expected_version, idempotency_key, "media_played"
    )
    if duplicate:
        return await get_match_state(session, match.id, user_id)
    question = await session.scalar(
        select(MatchQuestion)
        .where(MatchQuestion.id == question_id, MatchQuestion.match_id == match.id)
        .with_for_update()
    )
    if question is None or question.state != MatchQuestionState.OPEN:
        raise command_error("INVALID_STATE_TRANSITION", "The question is not open")
    if question.question_type_snapshot not in (QuestionType.AUDIO, QuestionType.VIDEO):
        raise command_error("INVALID_MEDIA_TYPE", "Only audio and video questions are played")
    if question.media_ready_at is None:
        raise command_error("MEDIA_NOT_READY", "The media must be ready before playback")
    if question.max_plays is not None and question.play_count >= question.max_plays:
        raise command_error("MEDIA_PLAY_LIMIT_REACHED", "The media play limit was reached")
    question.play_count += 1
    _record_event(
        session,
        match,
        user_id,
        idempotency_key,
        "media_played",
        {"match_question_id": str(question.id), "play_count": question.play_count},
    )
    await session.commit()
    return await get_match_state(session, match.id, user_id)


async def reveal_question(
    session: AsyncSession,
    match_id: UUID,
    question_id: UUID,
    user_id: UUID,
    expected_version: int,
    idempotency_key: str,
) -> MatchStateResponse:
    match, duplicate = await _begin_command(
        session, match_id, user_id, expected_version, idempotency_key, "question_revealed"
    )
    if duplicate:
        return await get_match_state(session, match.id, user_id)
    question = await session.scalar(
        select(MatchQuestion)
        .where(MatchQuestion.id == question_id, MatchQuestion.match_id == match.id)
        .with_for_update()
    )
    if question is None or question.state != MatchQuestionState.OPEN:
        raise command_error("INVALID_STATE_TRANSITION", "Only an open question can be revealed")
    question.state = MatchQuestionState.REVEALED
    question.revealed_at = now_utc()
    _record_event(
        session,
        match,
        user_id,
        idempotency_key,
        "question_revealed",
        {"match_question_id": str(question.id)},
    )
    await session.commit()
    return await get_match_state(session, match.id, user_id)


async def score_question(
    session: AsyncSession,
    match_id: UUID,
    question_id: UUID,
    user_id: UUID,
    expected_version: int,
    answered_by_team_no: int | None,
    idempotency_key: str,
) -> MatchStateResponse:
    match, duplicate = await _begin_command(
        session, match_id, user_id, expected_version, idempotency_key, "question_scored"
    )
    if duplicate:
        return await get_match_state(session, match.id, user_id)
    question = await session.scalar(
        select(MatchQuestion)
        .where(MatchQuestion.id == question_id, MatchQuestion.match_id == match.id)
        .with_for_update()
    )
    if question is None or question.state != MatchQuestionState.REVEALED:
        raise command_error("INVALID_STATE_TRANSITION", "Reveal the answer before scoring")
    if answered_by_team_no is not None:
        blocker = await session.scalar(
            select(MatchLifeline).where(
                MatchLifeline.match_id == match.id,
                MatchLifeline.lifeline_type == LifelineType.BLOCK_OPPONENT,
                MatchLifeline.match_question_id == question.id,
                MatchLifeline.state == LifelineState.USED,
            )
        )
        if blocker is not None and blocker.team_no != answered_by_team_no:
            raise command_error("TEAM_BLOCKED", "The opposing team is blocked on this question")
    doubled = await session.scalar(
        select(MatchLifeline.id).where(
            MatchLifeline.match_id == match.id,
            MatchLifeline.lifeline_type == LifelineType.DOUBLE_POINTS,
            MatchLifeline.match_question_id == question.id,
            MatchLifeline.state == LifelineState.USED,
        )
    )
    awarded = question.points * (2 if doubled is not None else 1) if answered_by_team_no else 0
    if answered_by_team_no is not None:
        team = await session.get(MatchTeam, (match.id, answered_by_team_no))
        if team is None:
            raise command_error("TEAM_NOT_FOUND", "The selected team does not exist")
        team.score += awarded
    question.state = MatchQuestionState.SCORED
    question.scored_at = now_utc()
    question.answered_by_team_no = answered_by_team_no
    question.awarded_points = awarded
    match.current_team_no = 2 if match.current_team_no == 1 else 1
    remaining = await session.scalar(
        select(func.count(MatchQuestion.id)).where(
            MatchQuestion.match_id == match.id,
            MatchQuestion.id != question.id,
            MatchQuestion.state != MatchQuestionState.SCORED,
        )
    )
    if not remaining:
        match.status = MatchStatus.COMPLETED
        match.finished_at = now_utc()
    _record_event(
        session,
        match,
        user_id,
        idempotency_key,
        "question_scored",
        {
            "match_question_id": str(question.id),
            "answered_by_team_no": answered_by_team_no,
            "awarded_points": awarded,
        },
    )
    await session.commit()
    return await get_match_state(session, match.id, user_id)


async def list_match_history(session: AsyncSession, user_id: UUID) -> MatchHistoryResponse:
    matches = (
        await session.scalars(
            select(Match)
            .where(Match.owner_id == user_id)
            .order_by(Match.created_at.desc())
            .limit(50)
        )
    ).all()
    if not matches:
        return MatchHistoryResponse(items=[])
    teams = (
        await session.scalars(
            select(MatchTeam)
            .where(MatchTeam.match_id.in_([match.id for match in matches]))
            .order_by(MatchTeam.match_id, MatchTeam.team_no)
        )
    ).all()
    by_match: dict[UUID, list[TeamState]] = {match.id: [] for match in matches}
    for team in teams:
        by_match[team.match_id].append(
            TeamState(team_no=team.team_no, name=team.name, score=team.score)
        )
    return MatchHistoryResponse(
        items=[
            MatchSummary(
                id=match.id,
                status=match.status,
                current_team_no=match.current_team_no,
                version=match.version,
                created_at=match.created_at,
                finished_at=match.finished_at,
                teams=by_match[match.id],
            )
            for match in matches
        ]
    )
