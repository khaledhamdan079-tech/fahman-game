from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MediaAsset, MediaKind, Question


def question_item(points: int, index: int) -> dict[str, object]:
    answer = f"الإجابة {points}-{index}"
    return {
        "category_name_ar": "معلومات عامة",
        "category_description_ar": "أسئلة متنوعة",
        "question_type": "text",
        "prompt_ar": f"السؤال {points}-{index}",
        "answer_ar": answer,
        "points": points,
        "options": [
            {"text_ar": answer, "is_correct": True, "sort_order": 0},
            {"text_ar": "إجابة غير صحيحة", "is_correct": False, "sort_order": 1},
        ],
    }


@pytest.mark.asyncio
async def test_admin_import_is_protected_idempotent_and_makes_category_eligible(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    payload = {
        "publish": True,
        "items": [question_item(points, index) for points in (200, 400, 600) for index in range(2)],
    }

    forbidden = await client.post("/v1/admin/import/questions", json=payload)
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "ADMIN_FORBIDDEN"

    imported = await client.post(
        "/v1/admin/import/questions",
        headers={"X-Admin-Key": "test-admin-key"},
        json=payload,
    )
    assert imported.status_code == 200, imported.text
    assert imported.json() == {
        "categories_created": 1,
        "questions_created": 6,
        "media_created": 0,
        "skipped_duplicates": 0,
    }

    repeated = await client.post(
        "/v1/admin/import/questions",
        headers={"X-Admin-Key": "test-admin-key"},
        json=payload,
    )
    assert repeated.status_code == 200
    assert repeated.json()["questions_created"] == 0
    assert repeated.json()["skipped_duplicates"] == 6

    eligible = await client.get("/v1/categories/eligible", headers=auth_headers)
    assert eligible.status_code == 200
    assert eligible.json()[0]["eligible"] is True
    assert eligible.json()[0]["unused_200"] == 2
    assert eligible.json()[0]["unused_400"] == 2
    assert eligible.json()[0]["unused_600"] == 2


@pytest.mark.asyncio
async def test_admin_import_rejects_invalid_correct_answer(client: AsyncClient) -> None:
    item = question_item(200, 1)
    item["answer_ar"] = "إجابة مختلفة"
    response = await client.post(
        "/v1/admin/import/questions",
        headers={"X-Admin-Key": "test-admin-key"},
        json={"items": [item]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_import_creates_audio_metadata_with_default_play_limit(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    item = question_item(400, 8)
    item.update(
        {
            "question_type": "audio",
            "media": {
                "kind": "audio",
                "storage_key": "questions/cars/engine.mp3",
                "mime_type": "audio/mpeg",
                "size_bytes": 4096,
                "duration_ms": 8000,
                "checksum_sha256": "c" * 64,
                "status": "ready",
            },
        }
    )
    response = await client.post(
        "/v1/admin/import/questions",
        headers={"X-Admin-Key": "test-admin-key"},
        json={"items": [item]},
    )
    assert response.status_code == 200, response.text
    assert response.json()["media_created"] == 1

    question = await session.scalar(select(Question))
    media = await session.scalar(select(MediaAsset))
    assert question is not None and question.max_plays == 2
    assert media is not None and media.kind == MediaKind.AUDIO
