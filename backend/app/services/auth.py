from __future__ import annotations

from datetime import UTC, datetime
from secrets import compare_digest
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import IssuedTokens, hash_device_secret, hash_refresh_token, issue_tokens
from app.db.models import DeviceCredential, RefreshToken, User
from app.services.google_auth import GoogleIdentity


async def find_or_create_google_user(session: AsyncSession, identity: GoogleIdentity) -> User:
    user = await session.scalar(select(User).where(User.google_subject == identity.subject))
    if user is None:
        user = User(
            google_subject=identity.subject,
            email=identity.email,
            display_name=identity.display_name,
            avatar_url=identity.avatar_url,
        )
        session.add(user)
        await session.flush()
    else:
        user.email = identity.email
        user.display_name = identity.display_name
        user.avatar_url = identity.avatar_url
    return user


async def find_or_create_device_user(
    session: AsyncSession,
    installation_id: UUID,
    device_secret: str,
    display_name: str,
    platform: str | None,
    *,
    now: datetime | None = None,
) -> User:
    timestamp = now or datetime.now(UTC)
    credential = await session.scalar(
        select(DeviceCredential).where(DeviceCredential.installation_id == installation_id)
    )
    secret_hash = hash_device_secret(device_secret)
    if credential is not None:
        if credential.revoked_at is not None or not compare_digest(
            credential.secret_hash, secret_hash
        ):
            raise AppError(
                "AUTH_DEVICE_INVALID",
                "The installation credentials are invalid",
                status_code=401,
            )
        user = await session.get(User, credential.user_id)
        if user is None:
            raise AppError(
                "AUTH_DEVICE_INVALID",
                "The installation credentials are invalid",
                status_code=401,
            )
        credential.last_seen_at = timestamp
        credential.platform = platform or credential.platform
        return user

    normalized_name = display_name.strip() or "لاعب فهمان"
    user = User(display_name=normalized_name)
    session.add(user)
    await session.flush()
    session.add(
        DeviceCredential(
            user_id=user.id,
            installation_id=installation_id,
            secret_hash=secret_hash,
            platform=platform,
            last_seen_at=timestamp,
        )
    )
    return user


async def attach_device_credential(
    session: AsyncSession,
    user: User,
    installation_id: UUID,
    device_secret: str,
    platform: str | None,
    *,
    now: datetime | None = None,
) -> None:
    timestamp = now or datetime.now(UTC)
    credential = await session.scalar(
        select(DeviceCredential).where(DeviceCredential.installation_id == installation_id)
    )
    secret_hash = hash_device_secret(device_secret)
    if credential is not None:
        if credential.user_id != user.id or not compare_digest(credential.secret_hash, secret_hash):
            raise AppError(
                "AUTH_DEVICE_ALREADY_ATTACHED",
                "This installation is already attached to another user",
                status_code=409,
            )
        credential.last_seen_at = timestamp
        credential.platform = platform or credential.platform
        await session.commit()
        return

    existing_for_user = await session.scalar(
        select(DeviceCredential).where(DeviceCredential.user_id == user.id)
    )
    if existing_for_user is not None:
        raise AppError(
            "AUTH_USER_ALREADY_HAS_DEVICE",
            "This user is already attached to an installation",
            status_code=409,
        )
    session.add(
        DeviceCredential(
            user_id=user.id,
            installation_id=installation_id,
            secret_hash=secret_hash,
            platform=platform,
            last_seen_at=timestamp,
        )
    )
    await session.commit()


async def create_session_tokens(
    session: AsyncSession,
    user: User,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> IssuedTokens:
    tokens = issue_tokens(user.id, settings, now=now)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(tokens.refresh_token),
            expires_at=tokens.refresh_expires_at,
        )
    )
    await session.commit()
    return tokens


async def rotate_refresh_token(
    session: AsyncSession,
    raw_token: str,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> tuple[User, IssuedTokens]:
    current_time = now or datetime.now(UTC)
    stored = await session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    if stored is None or stored.revoked_at is not None:
        raise AppError("AUTH_REFRESH_INVALID", "The refresh token is invalid", status_code=401)

    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= current_time:
        raise AppError("AUTH_REFRESH_INVALID", "The refresh token is invalid", status_code=401)

    user = await session.get(User, stored.user_id)
    if user is None:
        raise AppError("AUTH_REFRESH_INVALID", "The refresh token is invalid", status_code=401)

    stored.revoked_at = current_time
    tokens = issue_tokens(user.id, settings, now=current_time)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(tokens.refresh_token),
            expires_at=tokens.refresh_expires_at,
        )
    )
    await session.commit()
    return user, tokens


async def revoke_refresh_token(
    session: AsyncSession,
    raw_token: str,
    *,
    now: datetime | None = None,
) -> None:
    stored = await session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = now or datetime.now(UTC)
        await session.commit()
