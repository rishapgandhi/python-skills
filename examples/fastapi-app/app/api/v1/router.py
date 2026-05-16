"""V1 API router — aggregates all v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router

v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(users_router, prefix="/users", tags=["users"])
