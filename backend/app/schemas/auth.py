from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=20)


class DeviceSessionRequest(BaseModel):
    installation_id: UUID
    device_secret: str = Field(min_length=32, max_length=256)
    platform: str | None = Field(default=None, min_length=1, max_length=32)
    display_name: str = Field(default="لاعب فهمان", min_length=1, max_length=160)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr | None
    display_name: str
    avatar_url: str | None


class TokenResponse(BaseModel):
    token_type: str = "bearer"
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    user: UserResponse
