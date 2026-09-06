from __future__ import annotations

from httpx import AsyncClient

DEVICE_PAYLOAD = {
    "installation_id": "61bb06af-d5f8-4c67-94cb-d160f7196e46",
    "device_secret": "a-secure-random-device-secret-with-more-than-32-characters",
    "platform": "android",
    "display_name": "لاعب الاختبار",
}


async def test_device_session_is_idempotent_and_rejects_wrong_secret(
    client: AsyncClient,
) -> None:
    first = await client.post("/v1/auth/device/session", json=DEVICE_PAYLOAD)
    second = await client.post("/v1/auth/device/session", json=DEVICE_PAYLOAD)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["user"]["id"] == second.json()["user"]["id"]
    assert first.json()["user"]["email"] is None
    assert first.json()["user"]["display_name"] == "لاعب الاختبار"

    rejected = await client.post(
        "/v1/auth/device/session",
        json={
            **DEVICE_PAYLOAD,
            "device_secret": "a-different-device-secret-with-more-than-32-characters",
        },
    )
    assert rejected.status_code == 401
    assert rejected.json()["error"]["code"] == "AUTH_DEVICE_INVALID"


async def test_existing_google_user_can_attach_device(client: AsyncClient) -> None:
    login = await client.post(
        "/v1/auth/google",
        json={"id_token": "valid-google-id-token-for-tests"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    attached = await client.post("/v1/auth/device/attach", json=DEVICE_PAYLOAD, headers=headers)
    assert attached.status_code == 200

    restored = await client.post("/v1/auth/device/session", json=DEVICE_PAYLOAD)
    assert restored.status_code == 200
    assert restored.json()["user"]["id"] == login.json()["user"]["id"]


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
