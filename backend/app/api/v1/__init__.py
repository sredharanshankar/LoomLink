from fastapi import APIRouter
from app.api.v1 import auth, health, settings as settings_router

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(settings_router.router, prefix="/settings", tags=["settings"])