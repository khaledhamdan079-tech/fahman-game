from __future__ import annotations

from httpx import AsyncClient


async def test_google_login_creates_session_and_me_works(client: AsyncClient) -> None:
    login = await client.post(
        "/v1/auth/google",
        json={"id_token": "valid-google-id-token-for-tests"},
    )

    assert login.status_code == 200
    payload = login.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "player@example.com"
    assert payload["access_token"]
    assert payload["refresh_token"]

    profile = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["display_name"] == "Test Player"


async def test_refresh_rotates_token(client: AsyncClient) -> None:
    login = await client.post(
        "/v1/auth/google",
        json={"id_token": "valid-google-id-token-for-tests"},
    )
    old_refresh_token = login.json()["refresh_token"]

    refreshed = await client.post(
        "/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != old_refresh_token

    reused = await client.post(
        "/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "AUTH_REFRESH_INVALID"
