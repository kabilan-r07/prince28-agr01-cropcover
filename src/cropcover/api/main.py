"""App factory: build a fully wired FastAPI app from settings."""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from cropcover.api.errors import register_error_handlers
from cropcover.api.middleware import request_context
from cropcover.api.routes import documents, health
from cropcover.config import Settings, get_settings
from cropcover.db.session import make_engine, make_sessionmaker
from cropcover.logging_setup import setup_logging

logger = logging.getLogger("cropcover")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    engine = make_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("starting", extra={"status": settings.app_env})
        yield
        await engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)

    app.middleware("http")(request_context)
    register_error_handlers(app)

    v1 = APIRouter(prefix="/v1")
    v1.include_router(documents.router)

    app.include_router(health.router)
    app.include_router(v1)

    return app
