from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, status

from app.api.dependencies import CurrentUserDependency, SessionDependency
from app.db.models import LifelineType
from app.schemas.matches import (
    ArmLifelineRequest,
    MatchCommandRequest,
    MatchCreateRequest,
    MatchHistoryResponse,
    MatchStateResponse,
    ScoreQuestionRequest,
)
from app.services.matches import (
    arm_lifeline,
    cancel_armed_lifeline,
    cancel_match,
    create_match,
    get_active_match_state,
    get_match_state,
    list_match_history,
    mark_media_ready,
    open_question,
    record_media_play,
    reveal_question,
    score_question,
)

router = APIRouter(prefix="/matches", tags=["matches"])
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=255)]


@router.post("", response_model=MatchStateResponse, status_code=status.HTTP_201_CREATED)
async def new_match(
    payload: MatchCreateRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
    idempotency_key: IdempotencyKey,
) -> MatchStateResponse:
    return await create_match(session, user, payload, idempotency_key)


@router.get("", response_model=MatchHistoryResponse)
async def match_history(
    session: SessionDependency, user: CurrentUserDependency
) -> MatchHistoryResponse:
    return await list_match_history(session, user.id)


@router.get("/active", response_model=MatchStateResponse | None)
async def active_match(
    session: SessionDependency, user: CurrentUserDependency
) -> MatchStateResponse | None:
    return await get_active_match_state(session, user.id)


@router.get("/{match_id}", response_model=MatchStateResponse)
async def match_state(
    match_id: UUID, session: SessionDependency, user: CurrentUserDependency
) -> MatchStateResponse:
    return await get_match_state(session, match_id, user.id)


@router.post("/{match_id}/cancel", response_model=MatchStateResponse)
async def cancel_active_match(
    match_id: UUID,
    payload: MatchCommandRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
    idempotency_key: IdempotencyKey,
) -> MatchStateResponse:
    return await cancel_match(session, match_id, user.id, payload.expected_version, idempotency_key)


@router.post("/{match_id}/questions/{question_id}/open", response_model=MatchStateResponse)
async def open_match_question(
    match_id: UUID,
    question_id: UUID,
    payload: MatchCommandRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
    idempotency_key: IdempotencyKey,
) -> MatchStateResponse:
    return await open_question(
        session, match_id, question_id, user.id, payload.expected_version, idempotency_key
    )


@router.post("/{match_id}/questions/{question_id}/media-ready", response_model=MatchStateResponse)
async def media_ready(
    match_id: UUID,
    question_id: UUID,
    payload: MatchCommandRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
    idempotency_key: IdempotencyKey,
) -> MatchStateResponse:
    return await mark_media_ready(
        session, match_id, question_id, user.id, payload.expected_version, idempotency_key
    )


@router.post("/{match_id}/questions/{question_id}/play", response_model=MatchStateResponse)
async def play_media(
    match_id: UUID,
    question_id: UUID,
    payload: MatchCommandRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
    idempotency_key: IdempotencyKey,
) -> MatchStateResponse:
    return await record_media_play(
        session, match_id, question_id, user.id, payload.expected_version, idempotency_key
    )


@router.post("/{match_id}/questions/{question_id}/reveal", response_model=MatchStateResponse)
async def reveal_match_question(
    match_id: UUID,
    question_id: UUID,
    payload: MatchCommandRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
    idempotency_key: IdempotencyKey,
) -> MatchStateResponse:
    return await reveal_question(
        session, match_id, question_id, user.id, payload.expected_version, idempotency_key
    )


@router.post("/{match_id}/questions/{question_id}/score", response_model=MatchStateResponse)
async def score_match_question(
    match_id: UUID,
    question_id: UUID,
    payload: ScoreQuestionRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
    idempotency_key: IdempotencyKey,
) -> MatchStateResponse:
    return await score_question(
        session,
        match_id,
        question_id,
        user.id,
        payload.expected_version,
        payload.answered_by_team_no,
        idempotency_key,
    )


@router.post("/{match_id}/lifelines/{lifeline_type}/arm", response_model=MatchStateResponse)
async def use_lifeline(
    match_id: UUID,
    lifeline_type: LifelineType,
    payload: ArmLifelineRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
    idempotency_key: IdempotencyKey,
) -> MatchStateResponse:
    return await arm_lifeline(
        session,
        match_id,
        lifeline_type,
        payload.match_question_id,
        user.id,
        payload.expected_version,
        idempotency_key,
    )


@router.post("/{match_id}/lifelines/{lifeline_type}/cancel", response_model=MatchStateResponse)
async def cancel_lifeline(
    match_id: UUID,
    lifeline_type: LifelineType,
    payload: MatchCommandRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
    idempotency_key: IdempotencyKey,
) -> MatchStateResponse:
    return await cancel_armed_lifeline(
        session,
        match_id,
        lifeline_type,
        user.id,
        payload.expected_version,
        idempotency_key,
    )
