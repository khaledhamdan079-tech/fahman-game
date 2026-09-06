from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies import (
    AdminDependency,
    MediaUploadDependency,
    SessionDependency,
    SettingsDependency,
)
from app.schemas.admin import QuestionImportRequest, QuestionImportResponse
from app.schemas.media import (
    MediaUploadCompleteResponse,
    MediaUploadRequest,
    MediaUploadResponse,
)
from app.services.admin_import import import_questions
from app.services.media import complete_media_upload, create_media_upload

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/import/questions", response_model=QuestionImportResponse)
async def import_question_catalogue(
    payload: QuestionImportRequest,
    session: SessionDependency,
    _admin: AdminDependency,
) -> QuestionImportResponse:
    return await import_questions(session, payload)


@router.post(
    "/media/presign-upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def presign_media_upload(
    payload: MediaUploadRequest,
    session: SessionDependency,
    _admin: AdminDependency,
    storage: MediaUploadDependency,
    settings: SettingsDependency,
) -> MediaUploadResponse:
    return await create_media_upload(session, payload, storage, settings)


@router.post(
    "/media/{media_asset_id}/complete",
    response_model=MediaUploadCompleteResponse,
)
async def finish_media_upload(
    media_asset_id: UUID,
    session: SessionDependency,
    _admin: AdminDependency,
    storage: MediaUploadDependency,
) -> MediaUploadCompleteResponse:
    return await complete_media_upload(session, media_asset_id, storage)
