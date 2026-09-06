from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.db.models import LifelineState, LifelineType, MatchQuestionState, MatchStatus, QuestionType


class MatchCreateRequest(BaseModel):
    category_ids: list[UUID] = Field(min_length=3, max_length=7)
    team_one_name: str = Field(min_length=1, max_length=160)
    team_two_name: str = Field(min_length=1, max_length=160)
    timer_seconds: int = Field(default=60, ge=10, le=300)

    @field_validator("category_ids")
    @classmethod
    def categories_must_be_unique(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("category_ids must be unique")
        return value

    @field_validator("team_one_name", "team_two_name")
    @classmethod
    def normalize_team_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("team name cannot be blank")
        return normalized


class MatchCommandRequest(BaseModel):
    expected_version: int = Field(ge=1)


class ScoreQuestionRequest(MatchCommandRequest):
    answered_by_team_no: int | None = Field(default=None, ge=1, le=2)


class ArmLifelineRequest(MatchCommandRequest):
    match_question_id: UUID


class TeamState(BaseModel):
    team_no: int
    name: str
    score: int


class LifelineView(BaseModel):
    team_no: int
    lifeline_type: LifelineType
    state: LifelineState
    match_question_id: UUID | None


class BoardQuestion(BaseModel):
    id: UUID
    points: int
    question_type: QuestionType
    state: MatchQuestionState
    play_count: int
    max_plays: int | None
    choosing_team_no: int | None
    answered_by_team_no: int | None
    awarded_points: int


class MatchCategoryView(BaseModel):
    id: UUID
    name_ar: str
    position: int
    questions: list[BoardQuestion]


class ActiveQuestion(BaseModel):
    id: UUID
    question_type: QuestionType
    prompt_ar: str
    options: list[dict[str, object]]
    answer_ar: str | None
    points: int
    effective_points: int
    state: MatchQuestionState
    media_asset_id: UUID | None
    media_ready_at: datetime | None
    deadline_at: datetime | None
    play_count: int
    max_plays: int | None
    choosing_team_no: int | None


class MatchStateResponse(BaseModel):
    id: UUID
    status: MatchStatus
    current_team_no: int
    timer_seconds: int
    version: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    teams: list[TeamState]
    categories: list[MatchCategoryView]
    lifelines: list[LifelineView]
    active_question: ActiveQuestion | None


class MatchSummary(BaseModel):
    id: UUID
    status: MatchStatus
    current_team_no: int
    version: int
    created_at: datetime
    finished_at: datetime | None
    teams: list[TeamState]


class MatchHistoryResponse(BaseModel):
    items: list[MatchSummary]
