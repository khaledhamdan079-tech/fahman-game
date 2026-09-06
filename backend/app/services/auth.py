from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import IssuedTokens, hash_refresh_token, issue_tokens
from app.db.models import RefreshToken, User
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
