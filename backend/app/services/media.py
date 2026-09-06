from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AppError
from app.db.models import (
    Match,
    MatchQuestion,
    MatchQuestionState,
    MediaAsset,
    MediaKind,
    MediaStatus,
)
from app.schemas.media import (
    MediaPlaybackResponse,
    MediaUploadCompleteResponse,
    MediaUploadRequest,
    MediaUploadResponse,
)


class MediaUrlSigner(Protocol):
    def sign(self, storage_key: str, expires_seconds: int) -> str: ...


class S3MediaUrlSigner:
    def __init__(self, settings: Settings) -> None:
        if not settings.media_storage_configured:
            raise AppError(
                "MEDIA_STORAGE_NOT_CONFIGURED", "Media storage is not configured", status_code=503
            )
        self.bucket = settings.media_bucket or ""
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.media_endpoint_url,
            region_name=settings.media_region,
            aws_access_key_id=settings.media_access_key_id,
            aws_secret_access_key=settings.media_secret_access_key,
        )

    def sign(self, storage_key: str, expires_seconds: int) -> str:
        return str(
            self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_key},
                ExpiresIn=expires_seconds,
            )
        )


@dataclass(frozen=True)
class UploadedObjectMetadata:
    size_bytes: int
    mime_type: str
    checksum_sha256: str | None


class MediaUploadStorage(Protocol):
    def presign_upload(
        self,
        storage_key: str,
        mime_type: str,
        checksum_sha256: str,
        expires_seconds: int,
    ) -> str: ...

    def inspect(self, storage_key: str) -> UploadedObjectMetadata | None: ...


class S3MediaUploadStorage:
    def __init__(self, settings: Settings) -> None:
        if not settings.media_storage_configured:
            raise AppError(
                "MEDIA_STORAGE_NOT_CONFIGURED",
                "Media storage is not configured",
                status_code=503,
            )
        self.bucket = settings.media_bucket or ""
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.media_endpoint_url,
            region_name=settings.media_region,
            aws_access_key_id=settings.media_access_key_id,
            aws_secret_access_key=settings.media_secret_access_key,
        )

    def presign_upload(
        self,
        storage_key: str,
        mime_type: str,
        checksum_sha256: str,
        expires_seconds: int,
    ) -> str:
        return str(
            self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": storage_key,
                    "ContentType": mime_type,
                    "Metadata": {"sha256": checksum_sha256},
                },
                ExpiresIn=expires_seconds,
            )
        )

    def inspect(self, storage_key: str) -> UploadedObjectMetadata | None:
        try:
            result = self.client.head_object(Bucket=self.bucket, Key=storage_key)
        except ClientError as error:
            code = str(error.response.get("Error", {}).get("Code", ""))
            if code in ("404", "NoSuchKey", "NotFound"):
                return None
            raise
        metadata = result.get("Metadata", {})
        return UploadedObjectMetadata(
            size_bytes=int(result["ContentLength"]),
            mime_type=str(result.get("ContentType", "")),
            checksum_sha256=metadata.get("sha256"),
        )


MEDIA_MIME_EXTENSIONS: dict[MediaKind, dict[str, str]] = {
    MediaKind.IMAGE: {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    },
    MediaKind.AUDIO: {
        "audio/mpeg": "mp3",
        "audio/mp4": "m4a",
        "audio/ogg": "ogg",
        "audio/wav": "wav",
    },
    MediaKind.VIDEO: {
        "video/mp4": "mp4",
        "video/webm": "webm",
    },
}


def _upload_size_limit(settings: Settings, kind: MediaKind) -> int:
    return {
        MediaKind.IMAGE: settings.media_max_image_bytes,
        MediaKind.AUDIO: settings.media_max_audio_bytes,
        MediaKind.VIDEO: settings.media_max_video_bytes,
    }[kind]


async def create_media_upload(
    session: AsyncSession,
    request: MediaUploadRequest,
    storage: MediaUploadStorage,
    settings: Settings,
) -> MediaUploadResponse:
    mime_type = request.mime_type.lower().strip()
    extension = MEDIA_MIME_EXTENSIONS[request.kind].get(mime_type)
    if extension is None:
        raise AppError(
            "MEDIA_TYPE_NOT_ALLOWED",
            "The file type is not allowed for this media kind",
            status_code=422,
        )
    if request.size_bytes > _upload_size_limit(settings, request.kind):
        raise AppError(
            "MEDIA_TOO_LARGE",
            "The media file exceeds the configured size limit",
            status_code=413,
        )
    checksum = request.checksum_sha256.lower()
    existing = await session.scalar(
        select(MediaAsset).where(MediaAsset.checksum_sha256 == checksum)
    )
    if existing is not None:
        if (
            existing.status == MediaStatus.PENDING
            and existing.kind == request.kind
            and existing.mime_type == mime_type
            and existing.size_bytes == request.size_bytes
        ):
            return MediaUploadResponse(
                media_asset_id=existing.id,
                storage_key=existing.storage_key,
                upload_url=storage.presign_upload(
                    existing.storage_key,
                    mime_type,
                    checksum,
                    settings.media_upload_url_seconds,
                ),
                required_headers={
                    "Content-Type": mime_type,
                    "x-amz-meta-sha256": checksum,
                },
                expires_at=datetime.now(UTC) + timedelta(seconds=settings.media_upload_url_seconds),
                status=existing.status,
            )
        raise AppError(
            "MEDIA_ALREADY_EXISTS",
            "Media with this checksum already exists",
            status_code=409,
            details={"media_asset_id": str(existing.id), "status": existing.status.value},
        )

    media_id = uuid4()
    storage_key = f"questions/{request.kind.value}/{media_id}.{extension}"
    media = MediaAsset(
        id=media_id,
        kind=request.kind,
        storage_key=storage_key,
        mime_type=mime_type,
        size_bytes=request.size_bytes,
        duration_ms=request.duration_ms,
        width=request.width,
        height=request.height,
        checksum_sha256=checksum,
        status=MediaStatus.PENDING,
    )
    session.add(media)
    upload_url = storage.presign_upload(
        storage_key,
        mime_type,
        checksum,
        settings.media_upload_url_seconds,
    )
    await session.commit()
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.media_upload_url_seconds)
    return MediaUploadResponse(
        media_asset_id=media.id,
        storage_key=storage_key,
        upload_url=upload_url,
        required_headers={
            "Content-Type": mime_type,
            "x-amz-meta-sha256": checksum,
        },
        expires_at=expires_at,
        status=media.status,
    )


async def complete_media_upload(
    session: AsyncSession,
    media_asset_id: UUID,
    storage: MediaUploadStorage,
) -> MediaUploadCompleteResponse:
    media = await session.get(MediaAsset, media_asset_id)
    if media is None:
        raise AppError("MEDIA_NOT_FOUND", "Media asset not found", status_code=404)
    if media.status == MediaStatus.READY:
        return MediaUploadCompleteResponse(media_asset_id=media.id, status=media.status)
    if media.status == MediaStatus.REJECTED:
        raise AppError("MEDIA_REJECTED", "This media upload was rejected", status_code=409)
    uploaded = storage.inspect(media.storage_key)
    if uploaded is None:
        raise AppError(
            "MEDIA_UPLOAD_INCOMPLETE",
            "The uploaded object is not available yet",
            status_code=409,
        )
    mismatch = (
        uploaded.size_bytes != media.size_bytes
        or uploaded.mime_type.lower().split(";", 1)[0] != media.mime_type.lower()
        or uploaded.checksum_sha256 is None
        or uploaded.checksum_sha256.lower() != media.checksum_sha256.lower()
    )
    if mismatch:
        media.status = MediaStatus.REJECTED
        await session.commit()
        raise AppError(
            "MEDIA_UPLOAD_MISMATCH",
            "The uploaded object does not match the declared metadata",
            status_code=409,
        )
    media.status = MediaStatus.READY
    await session.commit()
    return MediaUploadCompleteResponse(media_asset_id=media.id, status=media.status)


async def authorize_playback(
    session: AsyncSession,
    match_id: UUID,
    media_asset_id: UUID,
    user_id: UUID,
    signer: MediaUrlSigner,
    expires_seconds: int,
) -> MediaPlaybackResponse:
    row = (
        await session.execute(
            select(MatchQuestion, MediaAsset)
            .join(Match, Match.id == MatchQuestion.match_id)
            .join(MediaAsset, MediaAsset.id == MatchQuestion.media_asset_id_snapshot)
            .where(
                Match.id == match_id,
                Match.owner_id == user_id,
                MatchQuestion.media_asset_id_snapshot == media_asset_id,
                MatchQuestion.state.in_((MatchQuestionState.OPEN, MatchQuestionState.REVEALED)),
                MediaAsset.status == MediaStatus.READY,
            )
        )
    ).first()
    if row is None:
        raise AppError(
            "MEDIA_NOT_AUTHORIZED", "Media is unavailable for this match", status_code=404
        )
    question, media = row
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_seconds)
    return MediaPlaybackResponse(
        media_asset_id=media.id,
        url=signer.sign(media.storage_key, expires_seconds),
        poster_url=(
            signer.sign(media.poster_storage_key, expires_seconds)
            if media.poster_storage_key
            else None
        ),
        mime_type=media.mime_type,
        duration_ms=media.duration_ms,
        expires_at=expires_at,
        max_plays=question.max_plays,
    )
