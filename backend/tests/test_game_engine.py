from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Category,
    MediaAsset,
    MediaKind,
    MediaStatus,
    Question,
    QuestionOption,
    QuestionStatus,
    QuestionType,
    UserQuestionUsage,
)


async def seed_catalogue(session: AsyncSession, *, with_audio: bool = False) -> list[UUID]:
    category_ids: list[UUID] = []
    audio_asset: MediaAsset | None = None
    if with_audio:
        audio_asset = MediaAsset(
            kind=MediaKind.AUDIO,
            storage_key="questions/car-engine.mp3",
            mime_type="audio/mpeg",
            size_bytes=2048,
            duration_ms=8000,
            checksum_sha256="a" * 64,
            status=MediaStatus.READY,
        )
        session.add(audio_asset)
        await session.flush()

    for category_index in range(3):
        category = Category(
            name_ar=f"فئة {category_index + 1}",
            description_ar="أسئلة تجريبية",
            is_active=True,
        )
        session.add(category)
        await session.flush()
        category_ids.append(category.id)
        for points in (200, 400, 600):
            for question_index in range(2):
                is_audio = bool(
                    with_audio and category_index == 0 and points == 200 and question_index == 0
                )
                question = Question(
                    category_id=category.id,
                    question_type=QuestionType.AUDIO if is_audio else QuestionType.TEXT,
                    prompt_ar=f"سؤال {category_index}-{points}-{question_index}",
                    answer_ar="الإجابة الصحيحة",
                    points=points,
                    media_asset_id=audio_asset.id if is_audio and audio_asset else None,
                    max_plays=2 if is_audio else None,
                    status=QuestionStatus.PUBLISHED,
                )
                session.add(question)
                await session.flush()
                session.add_all(
                    [
                        QuestionOption(
                            question_id=question.id,
                            text_ar="الإجابة الصحيحة",
                            is_correct=True,
                            sort_order=0,
                        ),
                        QuestionOption(
                            question_id=question.id,
                            text_ar="إجابة أخرى",
                            is_correct=False,
                            sort_order=1,
                        ),
                    ]
                )
    await session.commit()
    return category_ids


async def create_match(
    client: AsyncClient,
    auth_headers: dict[str, str],
    category_ids: list[UUID],
    *,
    key: str = "create-match-001",
) -> dict[str, object]:
    response = await client.post(
        "/v1/matches",
        headers={**auth_headers, "Idempotency-Key": key},
        json={
            "category_ids": [str(item) for item in category_ids],
            "team_one_name": "الصقور",
            "team_two_name": "الأبطال",
            "timer_seconds": 60,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def first_question(match: dict[str, object]) -> dict[str, object]:
    categories = match["categories"]
    assert isinstance(categories, list)
    return categories[0]["questions"][0]


@pytest.mark.asyncio
async def test_availability_and_match_creation_are_complete_and_idempotent(
    client: AsyncClient,
    session: AsyncSession,
    auth_headers: dict[str, str],
) -> None:
    no_active_match = await client.get("/v1/matches/active", headers=auth_headers)
    assert no_active_match.status_code == 200
    assert no_active_match.json() is None

    category_ids = await seed_catalogue(session)
    availability = await client.get("/v1/categories/eligible", headers=auth_headers)
    assert availability.status_code == 200
    assert len(availability.json()) == 3
    assert availability.json()[0]["unused_200"] == 2
    assert availability.json()[0]["complete_matches_possible"] == 1

    created = await create_match(client, auth_headers, category_ids)
    assert created["status"] == "active"
    assert len(created["categories"]) == 3
    assert sum(len(category["questions"]) for category in created["categories"]) == 18
    assert created["active_question"] is None

    active_match = await client.get("/v1/matches/active", headers=auth_headers)
    assert active_match.status_code == 200
    assert active_match.json()["id"] == created["id"]

    repeated = await create_match(client, auth_headers, category_ids)
    assert repeated["id"] == created["id"]
    assert repeated["version"] == 1

    after_reservation = await client.get("/v1/categories/eligible", headers=auth_headers)
    assert all(not item["eligible"] for item in after_reservation.json())

    cancelled = await client.post(
        f"/v1/matches/{created['id']}/cancel",
        headers={**auth_headers, "Idempotency-Key": "cancel-match-001"},
        json={"expected_version": 1},
    )
    assert cancelled.json()["status"] == "cancelled"
    assert (await client.get("/v1/matches/active", headers=auth_headers)).json() is None
    released = await client.get("/v1/categories/eligible", headers=auth_headers)
    assert all(item["eligible"] for item in released.json())


@pytest.mark.asyncio
async def test_question_flow_hides_answer_marks_usage_and_scores_once(
    client: AsyncClient,
    session: AsyncSession,
    auth_headers: dict[str, str],
) -> None:
    match = await create_match(client, auth_headers, await seed_catalogue(session))
    question = first_question(match)
    url = f"/v1/matches/{match['id']}/questions/{question['id']}"

    opened_response = await client.post(
        f"{url}/open",
        headers={**auth_headers, "Idempotency-Key": "open-question-001"},
        json={"expected_version": 1},
    )
    assert opened_response.status_code == 200
    opened = opened_response.json()
    assert opened["active_question"]["prompt_ar"].startswith("سؤال")
    assert opened["active_question"]["answer_ar"] is None
    assert opened["active_question"]["options_visible"] is False
    assert opened["active_question"]["options"] == []
    usage_count = await session.scalar(select(func.count(UserQuestionUsage.question_id)))
    assert usage_count == 1

    duplicate = await client.post(
        f"{url}/open",
        headers={**auth_headers, "Idempotency-Key": "open-question-001"},
        json={"expected_version": 1},
    )
    assert duplicate.json()["version"] == 2

    revealed_response = await client.post(
        f"{url}/reveal",
        headers={**auth_headers, "Idempotency-Key": "reveal-question-001"},
        json={"expected_version": 2},
    )
    revealed = revealed_response.json()
    assert revealed["active_question"]["answer_ar"] == "الإجابة الصحيحة"
    assert revealed["active_question"]["options_visible"] is False
    assert revealed["active_question"]["options"] == []

    scored_response = await client.post(
        f"{url}/score",
        headers={**auth_headers, "Idempotency-Key": "score-question-001"},
        json={"expected_version": 3, "answered_by_team_no": 1},
    )
    scored = scored_response.json()
    assert scored["teams"][0]["score"] == question["points"]
    assert scored["current_team_no"] == 2
    assert scored["version"] == 4

    duplicate_score = await client.post(
        f"{url}/score",
        headers={**auth_headers, "Idempotency-Key": "score-question-001"},
        json={"expected_version": 3, "answered_by_team_no": 1},
    )
    assert duplicate_score.json()["teams"][0]["score"] == question["points"]
    assert duplicate_score.json()["version"] == 4

    history = await client.get("/v1/matches", headers=auth_headers)
    assert history.status_code == 200
    assert history.json()["items"][0]["id"] == match["id"]


@pytest.mark.asyncio
async def test_show_options_lifeline_reveals_safe_options_once(
    client: AsyncClient,
    session: AsyncSession,
    auth_headers: dict[str, str],
) -> None:
    match = await create_match(client, auth_headers, await seed_catalogue(session))
    question = first_question(match)
    match_url = f"/v1/matches/{match['id']}"
    question_url = f"{match_url}/questions/{question['id']}"
    opened = await client.post(
        f"{question_url}/open",
        headers={**auth_headers, "Idempotency-Key": "open-for-options-001"},
        json={"expected_version": 1},
    )

    shown = await client.post(
        f"{match_url}/lifelines/show_options/arm",
        headers={**auth_headers, "Idempotency-Key": "show-options-001"},
        json={
            "expected_version": opened.json()["version"],
            "match_question_id": question["id"],
        },
    )

    assert shown.status_code == 200
    active = shown.json()["active_question"]
    assert active["options_visible"] is True
    assert [option["text_ar"] for option in active["options"]] == [
        "الإجابة الصحيحة",
        "إجابة أخرى",
    ]
    assert all("is_correct" not in option for option in active["options"])

    second = await client.post(
        f"{match_url}/lifelines/show_options/arm",
        headers={**auth_headers, "Idempotency-Key": "show-options-002"},
        json={
            "expected_version": shown.json()["version"],
            "match_question_id": question["id"],
        },
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "LIFELINE_ALREADY_USED"


@pytest.mark.asyncio
async def test_complete_three_category_match_finishes_with_consistent_scores(
    client: AsyncClient,
    session: AsyncSession,
    auth_headers: dict[str, str],
) -> None:
    match = await create_match(
        client,
        auth_headers,
        await seed_catalogue(session),
        key="complete-match-001",
    )
    question_ids = [
        question["id"] for category in match["categories"] for question in category["questions"]
    ]

    for index, question_id in enumerate(question_ids):
        question_url = f"/v1/matches/{match['id']}/questions/{question_id}"
        opened = await client.post(
            f"{question_url}/open",
            headers={**auth_headers, "Idempotency-Key": f"e2e-open-{index:02d}"},
            json={"expected_version": match["version"]},
        )
        assert opened.status_code == 200, opened.text
        match = opened.json()
        revealed = await client.post(
            f"{question_url}/reveal",
            headers={**auth_headers, "Idempotency-Key": f"e2e-reveal-{index:02d}"},
            json={"expected_version": match["version"]},
        )
        assert revealed.status_code == 200, revealed.text
        match = revealed.json()
        scored = await client.post(
            f"{question_url}/score",
            headers={**auth_headers, "Idempotency-Key": f"e2e-score-{index:02d}"},
            json={
                "expected_version": match["version"],
                "answered_by_team_no": match["current_team_no"],
            },
        )
        assert scored.status_code == 200, scored.text
        match = scored.json()

    assert match["status"] == "completed"
    assert match["active_question"] is None
    assert [team["score"] for team in match["teams"]] == [3600, 3600]
    assert sum(team["score"] for team in match["teams"]) == 7200
    usage_count = await session.scalar(select(func.count(UserQuestionUsage.question_id)))
    assert usage_count == 18
    assert (await client.get("/v1/matches/active", headers=auth_headers)).json() is None


@pytest.mark.asyncio
async def test_double_points_and_stale_version_protection(
    client: AsyncClient,
    session: AsyncSession,
    auth_headers: dict[str, str],
) -> None:
    match = await create_match(client, auth_headers, await seed_catalogue(session))
    question = first_question(match)
    match_url = f"/v1/matches/{match['id']}"
    question_url = f"{match_url}/questions/{question['id']}"

    armed = await client.post(
        f"{match_url}/lifelines/double_points/arm",
        headers={**auth_headers, "Idempotency-Key": "double-points-001"},
        json={"expected_version": 1, "match_question_id": question["id"]},
    )
    assert armed.status_code == 200
    assert first_question(armed.json())["state"] == "prepared"

    stale = await client.post(
        f"{question_url}/open",
        headers={**auth_headers, "Idempotency-Key": "open-question-stale"},
        json={"expected_version": 1},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "STALE_MATCH_VERSION"
    assert stale.json()["error"]["details"]["current_version"] == 2

    opened = await client.post(
        f"{question_url}/open",
        headers={**auth_headers, "Idempotency-Key": "open-question-002"},
        json={"expected_version": 2},
    )
    assert opened.json()["active_question"]["effective_points"] == question["points"] * 2
    revealed = await client.post(
        f"{question_url}/reveal",
        headers={**auth_headers, "Idempotency-Key": "reveal-question-002"},
        json={"expected_version": 3},
    )
    scored = await client.post(
        f"{question_url}/score",
        headers={**auth_headers, "Idempotency-Key": "score-question-002"},
        json={"expected_version": revealed.json()["version"], "answered_by_team_no": 1},
    )
    assert scored.json()["teams"][0]["score"] == question["points"] * 2


@pytest.mark.asyncio
async def test_audio_ready_play_limit_and_authorized_signed_url(
    client: AsyncClient,
    session: AsyncSession,
    auth_headers: dict[str, str],
) -> None:
    match = await create_match(client, auth_headers, await seed_catalogue(session, with_audio=True))
    audio = next(
        question
        for category in match["categories"]
        for question in category["questions"]
        if question["question_type"] == "audio"
    )
    question_url = f"/v1/matches/{match['id']}/questions/{audio['id']}"
    opened = await client.post(
        f"{question_url}/open",
        headers={**auth_headers, "Idempotency-Key": "open-audio-001"},
        json={"expected_version": 1},
    )
    assert opened.json()["active_question"]["deadline_at"] is None
    media_id = opened.json()["active_question"]["media_asset_id"]

    playback = await client.get(
        f"/v1/matches/{match['id']}/media/{media_id}/playback", headers=auth_headers
    )
    assert playback.status_code == 200
    assert playback.json()["url"].startswith("https://media.example.test/")
    assert "storage_key" not in playback.json()

    ready = await client.post(
        f"{question_url}/media-ready",
        headers={**auth_headers, "Idempotency-Key": "audio-ready-001"},
        json={"expected_version": 2},
    )
    assert ready.json()["active_question"]["deadline_at"] is not None
    version = ready.json()["version"]
    for index in range(2):
        played = await client.post(
            f"{question_url}/play",
            headers={**auth_headers, "Idempotency-Key": f"audio-play-{index:03}"},
            json={"expected_version": version},
        )
        assert played.status_code == 200
        version = played.json()["version"]
    blocked = await client.post(
        f"{question_url}/play",
        headers={**auth_headers, "Idempotency-Key": "audio-play-999"},
        json={"expected_version": version},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "MEDIA_PLAY_LIMIT_REACHED"


@pytest.mark.asyncio
async def test_block_opponent_rejects_award_to_the_blocked_team(
    client: AsyncClient,
    session: AsyncSession,
    auth_headers: dict[str, str],
) -> None:
    match = await create_match(client, auth_headers, await seed_catalogue(session))
    question = first_question(match)
    match_url = f"/v1/matches/{match['id']}"
    question_url = f"{match_url}/questions/{question['id']}"
    opened = await client.post(
        f"{question_url}/open",
        headers={**auth_headers, "Idempotency-Key": "open-for-block-001"},
        json={"expected_version": 1},
    )
    blocked = await client.post(
        f"{match_url}/lifelines/block_opponent/arm",
        headers={**auth_headers, "Idempotency-Key": "block-opponent-001"},
        json={
            "expected_version": opened.json()["version"],
            "match_question_id": question["id"],
        },
    )
    revealed = await client.post(
        f"{question_url}/reveal",
        headers={**auth_headers, "Idempotency-Key": "reveal-after-block-001"},
        json={"expected_version": blocked.json()["version"]},
    )
    rejected = await client.post(
        f"{question_url}/score",
        headers={**auth_headers, "Idempotency-Key": "blocked-score-001"},
        json={
            "expected_version": revealed.json()["version"],
            "answered_by_team_no": 2,
        },
    )
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "TEAM_BLOCKED"

    no_one = await client.post(
        f"{question_url}/score",
        headers={**auth_headers, "Idempotency-Key": "blocked-no-one-001"},
        json={
            "expected_version": revealed.json()["version"],
            "answered_by_team_no": None,
        },
    )
    assert no_one.status_code == 200
    assert all(team["score"] == 0 for team in no_one.json()["teams"])
