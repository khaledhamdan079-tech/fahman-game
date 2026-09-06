from __future__ import annotations

from app.db.base import Base


def test_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "categories",
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
