from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.db.models import MediaKind, MediaStatus, OptionsRevealTiming, QuestionType


class ImportOption(BaseModel):
    text_ar: str = Field(min_length=1, max_length=500)
    is_correct: bool = False
    sort_order: int = Field(ge=0)


class ImportMedia(BaseModel):
    kind: MediaKind
    storage_key: str = Field(min_length=1, max_length=1024)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)
    checksum_sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    duration_ms: int | None = Field(default=None, gt=0)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    poster_storage_key: str | None = Field(default=None, max_length=1024)
    status: MediaStatus = MediaStatus.READY


class ImportQuestion(BaseModel):
    category_name_ar: str = Field(min_length=1, max_length=160)
    category_description_ar: str | None = None
    question_type: QuestionType = QuestionType.TEXT
    prompt_ar: str = Field(min_length=1)
    answer_ar: str = Field(min_length=1)
    points: Literal[200, 400, 600]
    options: list[ImportOption] = Field(min_length=2, max_length=4)
    media: ImportMedia | None = None
    media_asset_id: UUID | None = None
    options_reveal_timing: OptionsRevealTiming = OptionsRevealTiming.IMMEDIATE
    max_plays: int | None = Field(default=None, ge=1, le=10)

    @model_validator(mode="after")
    def validate_question(self) -> ImportQuestion:
        correct = [option for option in self.options if option.is_correct]
        if len(correct) != 1:
            raise ValueError("Each question must have exactly one correct option")
        if correct[0].text_ar.strip() != self.answer_ar.strip():
            raise ValueError("The correct option must match answer_ar")
        orders = [option.sort_order for option in self.options]
        if len(set(orders)) != len(orders):
            raise ValueError("Option sort_order values must be unique")
        if self.media is not None and self.media_asset_id is not None:
            raise ValueError("Use media or media_asset_id, not both")
        if self.question_type == QuestionType.TEXT and (
            self.media is not None or self.media_asset_id is not None
        ):
            raise ValueError("Text questions cannot include media")
        if self.question_type != QuestionType.TEXT:
            if self.media is None and self.media_asset_id is None:
                raise ValueError("Image, audio and video questions require media")
            if self.media is not None and self.media.kind.value != self.question_type.value:
                raise ValueError("Media kind must match question_type")
        return self


class QuestionImportRequest(BaseModel):
    items: list[ImportQuestion] = Field(min_length=1, max_length=500)
    publish: bool = True


class QuestionImportResponse(BaseModel):
    categories_created: int
    questions_created: int
    media_created: int
    skipped_duplicates: int
