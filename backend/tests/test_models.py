from __future__ import annotations

from app.db.base import Base
from app.db.models import DeviceCredential


def test_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "categories",
        "device_credentials",
        "match_categories",
        "match_events",
        "match_lifelines",
        "match_questions",
        "match_teams",
        "matches",
        "media_assets",
        "question_options",
        "questions",
        "refresh_tokens",
        "user_question_usage",
        "users",
    }


def test_device_credential_timestamps_are_timezone_aware() -> None:
    assert DeviceCredential.__table__.c.created_at.type.timezone is True
    assert DeviceCredential.__table__.c.last_seen_at.type.timezone is True
    assert DeviceCredential.__table__.c.revoked_at.type.timezone is True
