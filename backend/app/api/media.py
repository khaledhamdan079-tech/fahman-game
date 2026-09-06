from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import (
    CurrentUserDependency,
    MediaSignerDependency,
    SessionDependency,
    SettingsDependency,
)
from app.schemas.media import MediaPlaybackResponse
from app.services.media import authorize_playback

router = APIRouter(prefix="/matches", tags=["media"])


@router.get("/{match_id}/media/{media_asset_id}/playback", response_model=MediaPlaybackResponse)
async def media_playback(
    match_id: UUID,
    media_asset_id: UUID,
    session: SessionDependency,
    user: CurrentUserDependency,
    signer: MediaSignerDependency,
    settings: SettingsDependency,
) -> MediaPlaybackResponse:
    return await authorize_playback(
        session,
        match_id,
        media_asset_id,
        user.id,
        signer,
        settings.media_signed_url_seconds,
    )
