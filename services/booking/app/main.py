from .kafka_consumer import start_payment_consumer_loop
from fastapi import FastAPI
from .config import settings
from .db import get_pool, close_pool
from .routers import bookings, health
import structlog
import logging
from prometheus_fastapi_instrumentator import Instrumentator

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


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.service_name)
    app.include_router(health.router)
    app.include_router(bookings.router)

    # OpenAPI docs endpoint (default at /docs, /openapi.json)
    @app.get("/openapi", include_in_schema=False)
    async def custom_openapi():
        return app.openapi()

    Instrumentator().instrument(app).expose(app)

    @app.get("/")
    def root():
        return {"status": "ok", "service": "booking"}

    @app.on_event("startup")
    async def startup():
        await get_pool()
        start_payment_consumer_loop()

    @app.on_event("shutdown")
    async def shutdown():
        await close_pool()

    return app

app = create_app()