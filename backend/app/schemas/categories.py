from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class CategoryAvailability(BaseModel):
    id: UUID
    name_ar: str
    description_ar: str | None
    unused_200: int
    unused_400: int
    unused_600: int
    total_unused: int
    complete_matches_possible: int
    eligible: bool
