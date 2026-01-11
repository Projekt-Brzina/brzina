from fastapi import FastAPI
from .config import settings
from .db import get_pool, close_pool
from .routers import bookings, health


def create_app() -> FastAPI:
    app = FastAPI(title=settings.service_name)
    app.include_router(health.router)
    app.include_router(bookings.router)

    @app.on_event("startup")
    async def startup():
        await get_pool()

    @app.on_event("shutdown")
    async def shutdown():
        await close_pool()

    return app


app = create_app()