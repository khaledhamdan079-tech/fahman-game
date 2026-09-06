from __future__ import annotations

from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.matches import router as matches_router
from app.api.media import router as media_router

api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(matches_router)
api_router.include_router(media_router)
