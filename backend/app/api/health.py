from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.dependencies import SessionDependency, SettingsDependency
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
async def live(settings: SettingsDependency) -> HealthResponse:
    return HealthResponse(service=settings.app_name, version=settings.app_version)


@router.get("/ready", response_model=HealthResponse)
async def ready(
    settings: SettingsDependency,
    session: SessionDependency,
) -> HealthResponse:
    await session.execute(text("SELECT 1"))
    return HealthResponse(service=settings.app_name, version=settings.app_version)
