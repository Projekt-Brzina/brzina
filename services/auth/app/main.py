from fastapi import FastAPI
from .routers import auth, health
from .db import get_pool, close_pool
from .config import settings
from prometheus_fastapi_instrumentator import Instrumentator

def create_app():
    app = FastAPI(title=settings.service_name)

    app.include_router(health.router)
    app.include_router(auth.router)
    from .routers.tenants import router as tenants_router
    app.include_router(tenants_router)
    from .routers.users import router as users_router
    app.include_router(users_router)

    # OpenAPI docs endpoint (default at /docs, /openapi.json)
    @app.get("/openapi", include_in_schema=False)
    async def custom_openapi():
        return app.openapi()

    @app.on_event("startup")
    async def startup():
        await get_pool()

    @app.on_event("shutdown")
    async def shutdown():
        await close_pool()

    # Prometheus metrics
    Instrumentator().instrument(app).expose(app)

    return app

app = create_app()