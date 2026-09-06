from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class QuestionType(enum.StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class QuestionStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RETIRED = "retired"


class OptionsRevealTiming(enum.StrEnum):
    IMMEDIATE = "immediate"
    AFTER_MEDIA = "after_media"


class MediaKind(enum.StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class MediaStatus(enum.StrEnum):
    PENDING = "pending"
    READY = "ready"
    REJECTED = "rejected"


class MatchStatus(enum.StrEnum):
    SETUP = "setup"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class MatchQuestionState(enum.StrEnum):
    AVAILABLE = "available"
    PREPARED = "prepared"
    OPEN = "open"
    REVEALED = "revealed"
    SCORED = "scored"
    REPLACED = "replaced"


class LifelineType(enum.StrEnum):
    SHOW_OPTIONS = "show_options"
    DOUBLE_POINTS = "double_points"
    BLOCK_OPPONENT = "block_opponent"


class LifelineState(enum.StrEnum):
    AVAILABLE = "available"
    ARMED = "armed"
    USED = "used"


def enum_type(enum_class: type[enum.StrEnum], name: str) -> SAEnum:
    return SAEnum(
        enum_class,
        name=name,
        native_enum=False,
        values_callable=lambda items: [e.value for e in items],
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    google_subject: Mapped[str | None] = mapped_column(String(255), unique=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text)


class DeviceCredential(Base):
    __tablename__ = "device_credentials"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    installation_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="positive_size"),
        CheckConstraint("duration_ms IS NULL OR duration_ms > 0", name="positive_duration"),
        CheckConstraint("width IS NULL OR width > 0", name="positive_width"),
        CheckConstraint("height IS NULL OR height > 0", name="positive_height"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    kind: Mapped[MediaKind] = mapped_column(enum_type(MediaKind, "media_kind"), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    poster_storage_key: Mapped[str | None] = mapped_column(String(1024))
    checksum_sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[MediaStatus] = mapped_column(
        enum_type(MediaStatus, "media_status"),
        default=MediaStatus.PENDING,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name_ar: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    description_ar: Mapped[str | None] = mapped_column(Text)
    cover_media_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class Question(TimestampMixin, Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("points IN (200, 400, 600)", name="valid_points"),
        Index("ix_questions_category_points_status", "category_id", "points", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    question_type: Mapped[QuestionType] = mapped_column(
        enum_type(QuestionType, "question_type"),
        nullable=False,
    )
    prompt_ar: Mapped[str] = mapped_column(Text, nullable=False)
    answer_ar: Mapped[str] = mapped_column(Text, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    media_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="RESTRICT")
    )
    options_reveal_timing: Mapped[OptionsRevealTiming] = mapped_column(
        enum_type(OptionsRevealTiming, "options_reveal_timing"),
        default=OptionsRevealTiming.IMMEDIATE,
        nullable=False,
    )
    max_plays: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[QuestionStatus] = mapped_column(
        enum_type(QuestionStatus, "question_status"),
        default=QuestionStatus.DRAFT,
        nullable=False,
    )


class QuestionOption(Base):
    __tablename__ = "question_options"
    __table_args__ = (
        UniqueConstraint("question_id", "sort_order", name="uq_question_options_question_sort"),
        CheckConstraint("sort_order >= 0", name="nonnegative_sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text_ar: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint("current_team_no IN (1, 2)", name="valid_current_team"),
        CheckConstraint("timer_seconds BETWEEN 10 AND 300", name="valid_timer"),
        CheckConstraint("version >= 1", name="positive_version"),
        Index("ix_matches_owner_status", "owner_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[MatchStatus] = mapped_column(
        enum_type(MatchStatus, "match_status"),
        default=MatchStatus.SETUP,
        nullable=False,
    )
    current_team_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    timer_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class MatchTeam(Base):
    __tablename__ = "match_teams"
    __table_args__ = (
        CheckConstraint("team_no IN (1, 2)", name="valid_team"),
        CheckConstraint("score >= 0", name="nonnegative_score"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class MatchCategory(Base):
    __tablename__ = "match_categories"
    __table_args__ = (
        UniqueConstraint("match_id", "category_id", name="uq_match_categories_category"),
        UniqueConstraint("match_id", "position", name="uq_match_categories_position"),
        CheckConstraint("position BETWEEN 0 AND 6", name="valid_position"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)


class MatchQuestion(Base):
    __tablename__ = "match_questions"
    __table_args__ = (
        UniqueConstraint("match_id", "question_id", name="uq_match_questions_question"),
        UniqueConstraint(
            "match_id",
            "category_position",
            "slot_position",
            name="uq_match_questions_slot",
        ),
        CheckConstraint("category_position BETWEEN 0 AND 6", name="valid_category_position"),
        CheckConstraint("slot_position BETWEEN 0 AND 5", name="valid_slot_position"),
        CheckConstraint("points IN (200, 400, 600)", name="valid_points"),
        CheckConstraint("max_plays IS NULL OR max_plays > 0", name="positive_max_plays"),
        CheckConstraint("play_count >= 0", name="nonnegative_play_count"),
        CheckConstraint(
            "answered_by_team_no IS NULL OR answered_by_team_no IN (1, 2)",
            name="valid_answered_team",
        ),
        CheckConstraint(
            "choosing_team_no IS NULL OR choosing_team_no IN (1, 2)",
            name="valid_choosing_team",
        ),
        CheckConstraint("awarded_points >= 0", name="nonnegative_award"),
        Index("ix_match_questions_match_state", "match_id", "state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_position: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_position: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type_snapshot: Mapped[QuestionType] = mapped_column(
        enum_type(QuestionType, "match_question_type"),
        nullable=False,
    )
    prompt_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    answer_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    options_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    media_asset_id_snapshot: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="RESTRICT")
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[MatchQuestionState] = mapped_column(
        enum_type(MatchQuestionState, "match_question_state"),
        default=MatchQuestionState.AVAILABLE,
        nullable=False,
    )
    max_plays: Mapped[int | None] = mapped_column(Integer)
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    media_ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    choosing_team_no: Mapped[int | None] = mapped_column(Integer)
    answered_by_team_no: Mapped[int | None] = mapped_column(Integer)
    awarded_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class UserQuestionUsage(Base):
    __tablename__ = "user_question_usage"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    first_match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    first_used_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class MatchLifeline(Base):
    __tablename__ = "match_lifelines"
    __table_args__ = (
        CheckConstraint("team_no IN (1, 2)", name="valid_team"),
        UniqueConstraint(
            "match_id",
            "team_no",
            "lifeline_type",
            name="uq_match_lifelines_team_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_no: Mapped[int] = mapped_column(Integer, nullable=False)
    lifeline_type: Mapped[LifelineType] = mapped_column(
        enum_type(LifelineType, "lifeline_type"),
        nullable=False,
    )
    state: Mapped[LifelineState] = mapped_column(
        enum_type(LifelineState, "lifeline_state"),
        default=LifelineState.AVAILABLE,
        nullable=False,
    )
    match_question_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("match_questions.id", ondelete="SET NULL")
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MatchEvent(Base):
    __tablename__ = "match_events"
    __table_args__ = (
        UniqueConstraint("match_id", "sequence_no", name="uq_match_events_sequence"),
        UniqueConstraint("match_id", "idempotency_key", name="uq_match_events_idempotency"),
        CheckConstraint("sequence_no >= 1", name="positive_sequence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
