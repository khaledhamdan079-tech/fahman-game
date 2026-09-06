from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Response, status

from app.api.dependencies import (
    CurrentUserDependency,
    GoogleVerifierDependency,
    SessionDependency,
    SettingsDependency,
)
from app.schemas.auth import (
    DeviceSessionRequest,
    GoogleLoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import (
    attach_device_credential,
    create_session_tokens,
    find_or_create_device_user,
    find_or_create_google_user,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/device/session", response_model=TokenResponse)
async def device_session(
    payload: DeviceSessionRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> TokenResponse:
    user = await find_or_create_device_user(
        session,
        payload.installation_id,
        payload.device_secret,
        payload.display_name,
        payload.platform,
    )
    tokens = await create_session_tokens(session, user, settings)
    return TokenResponse(user=UserResponse.model_validate(user), **asdict(tokens))


@router.post("/device/attach", response_model=UserResponse)
async def attach_device(
    payload: DeviceSessionRequest,
    session: SessionDependency,
    user: CurrentUserDependency,
) -> UserResponse:
    await attach_device_credential(
        session,
        user,
        payload.installation_id,
        payload.device_secret,
        payload.platform,
    )
    return UserResponse.model_validate(user)


@router.post("/google", response_model=TokenResponse)
async def google_login(
    payload: GoogleLoginRequest,
    session: SessionDependency,
    settings: SettingsDependency,
    verifier: GoogleVerifierDependency,
) -> TokenResponse:
    identity = verifier.verify(payload.id_token)
    user = await find_or_create_google_user(session, identity)
    tokens = await create_session_tokens(session, user, settings)
    return TokenResponse(user=UserResponse.model_validate(user), **asdict(tokens))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_session(
    payload: RefreshRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> TokenResponse:
    user, tokens = await rotate_refresh_token(session, payload.refresh_token, settings)
    return TokenResponse(user=UserResponse.model_validate(user), **asdict(tokens))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest, session: SessionDependency) -> Response:
    await revoke_refresh_token(session, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUserDependency) -> UserResponse:
    return UserResponse.model_validate(user)
