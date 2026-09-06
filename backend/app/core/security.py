from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import Settings
from app.core.errors import AppError


@dataclass(frozen=True, slots=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


def issue_tokens(user_id: UUID, settings: Settings, *, now: datetime | None = None) -> IssuedTokens:
    issued_at = now or datetime.now(UTC)
    access_expires_at = issued_at + timedelta(minutes=settings.access_token_minutes)
    refresh_expires_at = issued_at + timedelta(days=settings.refresh_token_days)
    access_token = jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iat": issued_at,
            "exp": access_expires_at,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return IssuedTokens(
        access_token=access_token,
        refresh_token=secrets.token_urlsafe(48),
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )


def decode_access_token(token: str, settings: Settings) -> UUID:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "type", "iat", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise AppError(
            "AUTH_TOKEN_INVALID", "The access token is invalid", status_code=401
        ) from exc

    if payload.get("type") != "access":
        raise AppError("AUTH_TOKEN_INVALID", "The access token is invalid", status_code=401)

    try:
        return UUID(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise AppError(
            "AUTH_TOKEN_INVALID", "The access token is invalid", status_code=401
        ) from exc


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_device_secret(secret: str) -> str:
    """Hash a high-entropy installation secret before database storage."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()
