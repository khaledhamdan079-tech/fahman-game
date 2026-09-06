from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import CurrentUserDependency, SessionDependency
from app.schemas.categories import CategoryAvailability
from app.services.categories import list_category_availability

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/eligible", response_model=list[CategoryAvailability])
async def eligible_categories(
    session: SessionDependency, user: CurrentUserDependency
) -> list[CategoryAvailability]:
    return await list_category_availability(session, user.id)
