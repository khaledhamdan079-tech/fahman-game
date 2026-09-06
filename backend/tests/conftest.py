from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import (
    get_google_token_verifier,
    get_media_upload_storage,
    get_media_url_signer,
)
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.services.google_auth import GoogleIdentity
from app.services.media import UploadedObjectMetadata


class FakeGoogleTokenVerifier:
    def verify(self, token: str) -> GoogleIdentity:
        if token != "valid-google-id-token-for-tests":
            raise AssertionError("The test should only send the known fake token")
        return GoogleIdentity(
            subject="google-test-subject",
            email="player@example.com",
            display_name="Test Player",
            avatar_url="https://example.com/avatar.png",
        )


class FakeMediaUrlSigner:
    def sign(self, storage_key: str, expires_seconds: int) -> str:
        return f"https://media.example.test/{storage_key}?expires={expires_seconds}"


class FakeMediaUploadStorage:
    def __init__(self) -> None:
        self.objects: dict[str, UploadedObjectMetadata] = {}

    def presign_upload(
        self,
        storage_key: str,
        mime_type: str,
        checksum_sha256: str,
        expires_seconds: int,
    ) -> str:
        return f"https://uploads.example.test/{storage_key}?expires={expires_seconds}"

    def inspect(self, storage_key: str) -> UploadedObjectMetadata | None:
        return self.objects.get(storage_key)


@pytest_asyncio.fixture
async def fake_media_upload() -> FakeMediaUploadStorage:
    return FakeMediaUploadStorage()


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as database_session:
        yield database_session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    session: AsyncSession,
    fake_media_upload: FakeMediaUploadStorage,
) -> AsyncIterator[AsyncClient]:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        jwt_secret="test-secret-that-is-long-enough-for-hs256-signing",
        google_client_ids=["test-client-id"],
        admin_api_key="test-admin-key",
    )
    app = create_app(settings)

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_google_token_verifier] = FakeGoogleTokenVerifier
    app.dependency_overrides[get_media_url_signer] = FakeMediaUrlSigner
    app.dependency_overrides[get_media_upload_storage] = lambda: fake_media_upload

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as http_client:
        yield http_client


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/v1/auth/google",
        json={"id_token": "valid-google-id-token-for-tests"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
