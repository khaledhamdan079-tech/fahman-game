from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.db.models import MediaKind, MediaStatus


class MediaPlaybackResponse(BaseModel):
    media_asset_id: UUID
    url: str
    poster_url: str | None
    mime_type: str
    duration_ms: int | None
    expires_at: datetime
    max_plays: int | None


class MediaUploadRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    kind: MediaKind
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)
    checksum_sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    duration_ms: int | None = Field(default=None, gt=0)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_dimensions(self) -> MediaUploadRequest:
        if self.kind == MediaKind.IMAGE and (self.width is None or self.height is None):
            raise ValueError("Image uploads require width and height")
        if self.kind in (MediaKind.AUDIO, MediaKind.VIDEO) and self.duration_ms is None:
            raise ValueError("Audio and video uploads require duration_ms")
        if self.kind == MediaKind.VIDEO and (self.width is None or self.height is None):
            raise ValueError("Video uploads require width and height")
        return self


class MediaUploadResponse(BaseModel):
    media_asset_id: UUID
    storage_key: str
    upload_url: str
    required_headers: dict[str, str]
    expires_at: datetime
    status: MediaStatus


class MediaUploadCompleteResponse(BaseModel):
    media_asset_id: UUID
    status: MediaStatus
