from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.events import start_dispatcher, set_loop
import asyncio

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    set_loop(asyncio.get_event_loop())
    start_dispatcher()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="LoomLink API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    from app.api.v1 import router as v1_router
    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()