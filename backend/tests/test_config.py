from __future__ import annotations

import pytest

from app.core.config import Settings


def test_normalizes_railway_postgres_url() -> None:
    settings = Settings(
        database_url="postgresql://user:password@postgres.railway.internal:5432/railway"
    )

    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_splits_comma_separated_settings() -> None:
    settings = Settings(
        google_client_ids="android-id, web-id",
        cors_origins="https://app.example.com, http://localhost:8080",
    )

    assert settings.google_client_ids == ["android-id", "web-id"]
    assert settings.cors_origins == ["https://app.example.com", "http://localhost:8080"]


def test_production_requires_admin_and_private_media_configuration() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret="a-production-secret-that-is-long-enough",
        google_client_ids=["web-id"],
    )

    with pytest.raises(RuntimeError, match="ADMIN_API_KEY"):
        settings.validate_runtime()


def test_complete_production_configuration_passes_runtime_validation() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret="a-production-secret-that-is-long-enough",
        google_client_ids=["web-id"],
        admin_api_key="a-long-operator-secret",
        media_bucket="fahman-private",
        media_access_key_id="access-key",
        media_secret_access_key="secret-key",
    )

    settings.validate_runtime()
