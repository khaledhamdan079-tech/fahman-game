from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.security import decode_access_token, hash_refresh_token, issue_tokens


def test_access_token_round_trip() -> None:
    settings = Settings(jwt_secret="test-secret-that-is-long-enough-for-hs256-signing")
    user_id = uuid4()

    tokens = issue_tokens(user_id, settings, now=datetime.now(UTC))

    assert decode_access_token(tokens.access_token, settings) == user_id
    assert len(tokens.refresh_token) > 40


def test_refresh_token_hash_is_stable_and_not_plaintext() -> None:
    raw_token = "refresh-token-value"

    assert hash_refresh_token(raw_token) == hash_refresh_token(raw_token)
    assert hash_refresh_token(raw_token) != raw_token
