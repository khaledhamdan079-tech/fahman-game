from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "Fahman API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/v1"

    database_url: str = "sqlite+aiosqlite:///./fahman.db"
    database_echo: bool = False

    jwt_secret: str = Field(
        default="development-only-secret-change-before-production",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = Field(default=15, ge=5, le=60)
    refresh_token_days: int = Field(default=30, ge=1, le=365)

    google_client_ids: Annotated[list[str], NoDecode] = Field(default_factory=list)
    admin_api_key: str | None = None
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"]
    )

    media_bucket: str | None = None
    media_endpoint_url: str | None = None
    media_region: str = "auto"
    media_access_key_id: str | None = None
    media_secret_access_key: str | None = None
    media_signed_url_seconds: int = Field(default=600, ge=60, le=3600)
    media_upload_url_seconds: int = Field(default=900, ge=60, le=3600)
    media_max_image_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    media_max_audio_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    media_max_video_bytes: int = Field(default=100 * 1024 * 1024, gt=0)

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @field_validator("google_client_ids", "cors_origins", mode="before")
    @classmethod
    def split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def validate_runtime(self) -> None:
        if self.is_production and self.jwt_secret.startswith("development-"):
            raise RuntimeError("JWT_SECRET must be replaced in production")
        if self.is_production and not self.google_client_ids:
            raise RuntimeError("GOOGLE_CLIENT_IDS must be configured in production")
        if self.is_production and not self.admin_api_key:
            raise RuntimeError("ADMIN_API_KEY must be configured in production")
        if self.is_production and not self.media_storage_configured:
            raise RuntimeError("Private media storage must be configured in production")

    @property
    def media_storage_configured(self) -> bool:
        return all(
            (
                self.media_bucket,
                self.media_access_key_id,
                self.media_secret_access_key,
            )
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
