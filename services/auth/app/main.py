from fastapi import FastAPI
from .routers import auth, health
from .db import get_pool, close_pool
from .config import settings


def create_app():
    app = FastAPI(title=settings.service_name)

    app.include_router(health.router)
    app.include_router(auth.router)

    @app.on_event("startup")
    async def startup():
        await get_pool()

    @app.on_event("shutdown")
    async def shutdown():
        await close_pool()

    return app


app = create_app()