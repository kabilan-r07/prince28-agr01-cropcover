"""App factory: build a fully wired FastAPI app from settings."""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from cropcover.api.errors import register_error_handlers
from cropcover.api.middleware import request_context
from cropcover.api.routes import chat, documents, health
from cropcover.config import Settings, get_settings
from cropcover.db.llm_calls import make_recorder
from cropcover.db.session import make_engine, make_sessionmaker
from cropcover.llm.gateway import build_gateway
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
        await app.state.gateway.aclose()
        await engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)
    app.state.gateway = build_gateway(settings, recorder=make_recorder(app.state.sessionmaker))
    app.state.system_prompt = chat.load_prompt(settings.prompts_dir)

    app.middleware("http")(request_context)
    register_error_handlers(app)

    v1 = APIRouter(prefix="/v1")
    v1.include_router(documents.router)
    v1.include_router(chat.router)

    app.include_router(health.router)
    app.include_router(v1)

    return app
