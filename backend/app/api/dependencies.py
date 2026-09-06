from __future__ import annotations

from secrets import compare_digest
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db_session
from app.services.google_auth import DefaultGoogleTokenVerifier, GoogleTokenVerifier
from app.services.media import (
    MediaUploadStorage,
    MediaUrlSigner,
    S3MediaUploadStorage,
    S3MediaUrlSigner,
)

bearer_scheme = HTTPBearer(auto_error=False)

SettingsDependency = Annotated[Settings, Depends(get_settings)]
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


def get_google_token_verifier(settings: SettingsDependency) -> GoogleTokenVerifier:
    return DefaultGoogleTokenVerifier(settings)


GoogleVerifierDependency = Annotated[GoogleTokenVerifier, Depends(get_google_token_verifier)]


def get_media_url_signer(settings: SettingsDependency) -> MediaUrlSigner:
    return S3MediaUrlSigner(settings)


MediaSignerDependency = Annotated[MediaUrlSigner, Depends(get_media_url_signer)]


def get_media_upload_storage(settings: SettingsDependency) -> MediaUploadStorage:
    return S3MediaUploadStorage(settings)


MediaUploadDependency = Annotated[MediaUploadStorage, Depends(get_media_upload_storage)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: SettingsDependency,
    session: SessionDependency,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("AUTH_REQUIRED", "Authentication is required", status_code=401)
    user_id: UUID = decode_access_token(credentials.credentials, settings)
    user = await session.get(User, user_id)
    if user is None:
        raise AppError("AUTH_TOKEN_INVALID", "The access token is invalid", status_code=401)
    return user


CurrentUserDependency = Annotated[User, Depends(get_current_user)]


def require_admin_api_key(
    settings: SettingsDependency,
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
) -> None:
    if not settings.admin_api_key:
        raise AppError(
            "ADMIN_IMPORT_DISABLED",
            "The catalogue import endpoint is not configured",
            status_code=503,
        )
    if x_admin_key is None or not compare_digest(x_admin_key, settings.admin_api_key):
        raise AppError("ADMIN_FORBIDDEN", "The admin API key is invalid", status_code=403)


AdminDependency = Annotated[None, Depends(require_admin_api_key)]
