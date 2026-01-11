from fastapi import FastAPI
from .config import settings
from .db import get_pool, close_pool
from .routers import health, example


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.service_name,
        version="0.1.0",
    )

    # Routers
    app.include_router(health.router)
    app.include_router(example.router)

    @app.on_event("startup")
    async def startup_event():
        await get_pool()

    @app.on_event("shutdown")
    async def shutdown_event():
        await close_pool()

    return app


app = create_app()