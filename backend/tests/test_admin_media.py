from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MediaAsset, MediaStatus, Question
from app.services.media import UploadedObjectMetadata

ADMIN_HEADERS = {"X-Admin-Key": "test-admin-key"}


def audio_upload() -> dict[str, object]:
    return {
        "file_name": "engine.mp3",
        "kind": "audio",
        "mime_type": "audio/mpeg",
        "size_bytes": 4096,
        "checksum_sha256": "d" * 64,
        "duration_ms": 8000,
    }


@pytest.mark.asyncio
async def test_media_upload_is_private_verified_and_reusable_by_import(
    client: AsyncClient,
    session: AsyncSession,
    fake_media_upload,
) -> None:
    forbidden = await client.post("/v1/admin/media/presign-upload", json=audio_upload())
    assert forbidden.status_code == 403

    presigned = await client.post(
        "/v1/admin/media/presign-upload",
        headers=ADMIN_HEADERS,
        json=audio_upload(),
    )
    assert presigned.status_code == 201, presigned.text
    upload = presigned.json()
    assert upload["status"] == "pending"
    assert upload["required_headers"]["x-amz-meta-sha256"] == "d" * 64
    assert upload["storage_key"].startswith("questions/audio/")

    retried = await client.post(
        "/v1/admin/media/presign-upload",
        headers=ADMIN_HEADERS,
        json=audio_upload(),
    )
    assert retried.status_code == 201
    assert retried.json()["media_asset_id"] == upload["media_asset_id"]
    assert retried.json()["storage_key"] == upload["storage_key"]

    not_uploaded = await client.post(
        f"/v1/admin/media/{upload['media_asset_id']}/complete",
        headers=ADMIN_HEADERS,
    )
    assert not_uploaded.status_code == 409
    assert not_uploaded.json()["error"]["code"] == "MEDIA_UPLOAD_INCOMPLETE"

    fake_media_upload.objects[upload["storage_key"]] = UploadedObjectMetadata(
        size_bytes=4096,
        mime_type="audio/mpeg",
        checksum_sha256="d" * 64,
    )
    completed = await client.post(
        f"/v1/admin/media/{upload['media_asset_id']}/complete",
        headers=ADMIN_HEADERS,
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "ready"

    answer = "بورشه 911"
    imported = await client.post(
        "/v1/admin/import/questions",
        headers=ADMIN_HEADERS,
        json={
            "items": [
                {
                    "category_name_ar": "السيارات",
                    "question_type": "audio",
                    "prompt_ar": "ما السيارة صاحبة هذا الصوت؟",
                    "answer_ar": answer,
                    "points": 200,
                    "media_asset_id": upload["media_asset_id"],
                    "options": [
                        {"text_ar": answer, "is_correct": True, "sort_order": 0},
                        {"text_ar": "سيارة أخرى", "is_correct": False, "sort_order": 1},
                    ],
                }
            ]
        },
    )
    assert imported.status_code == 200, imported.text
    question = next(iter((await session.execute(Question.__table__.select())).mappings()))
    assert str(question["media_asset_id"]) == upload["media_asset_id"]


@pytest.mark.asyncio
async def test_media_upload_rejects_metadata_mismatch(
    client: AsyncClient,
    session: AsyncSession,
    fake_media_upload,
) -> None:
    payload = audio_upload()
    payload["checksum_sha256"] = "e" * 64
    presigned = await client.post(
        "/v1/admin/media/presign-upload",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    upload = presigned.json()
    fake_media_upload.objects[upload["storage_key"]] = UploadedObjectMetadata(
        size_bytes=1,
        mime_type="audio/mpeg",
        checksum_sha256="e" * 64,
    )

    completed = await client.post(
        f"/v1/admin/media/{upload['media_asset_id']}/complete",
        headers=ADMIN_HEADERS,
    )
    assert completed.status_code == 409
    assert completed.json()["error"]["code"] == "MEDIA_UPLOAD_MISMATCH"
    media = await session.get(MediaAsset, UUID(upload["media_asset_id"]))
    assert media is not None and media.status == MediaStatus.REJECTED
