from fastapi import FastAPI
from .config import settings
from .db import get_pool, close_pool
from .routers import bookings, health
import structlog
import logging

def setup_logging():
    logging.basicConfig(format="%(message)s", stream=None, level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

from prometheus_fastapi_instrumentator import Instrumentator

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.service_name)
    app.include_router(health.router)
    app.include_router(bookings.router)

    Instrumentator().instrument(app).expose(app)

    @app.on_event("startup")
    async def startup():
        await get_pool()

    @app.on_event("shutdown")
    async def shutdown():
        await close_pool()

    return app

app = create_app()