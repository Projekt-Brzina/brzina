from fastapi import FastAPI, APIRouter
from .routers import cars, health
from .db import get_pool, close_pool
from .config import settings
import httpx
import strawberry
from strawberry.fastapi import GraphQLRouter
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

weather_router = APIRouter()

@weather_router.get("/weather/{city}")
async def get_weather(city: str):
    api_key = settings.weather_api_key
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return {"error": "Failed to fetch weather"}
        data = resp.json()
        return {
            "city": city,
            "temp": data["main"]["temp"],
            "desc": data["weather"][0]["description"]
        }

# GraphQL schema for cars
@strawberry.type
class CarType:
    id: int
    brand: str
    model: str
    plate: str
    hourly_rate: int
    owner_user_id: int
    tenant_id: int

import asyncio
from .db import get_pool

@strawberry.type
class Query:
    @strawberry.field
    async def cars(self, tenant_id: int) -> list[CarType]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, brand, model, plate, hourly_rate, owner_user_id, tenant_id
                FROM cars
                WHERE tenant_id=$1
                """,
                tenant_id
            )
        return [CarType(**dict(r)) for r in rows]

schema = strawberry.Schema(Query)
graphql_app = GraphQLRouter(schema)

def create_app():
    setup_logging()
    app = FastAPI(title=settings.service_name)

    app.include_router(health.router)
    app.include_router(cars.router)
    app.include_router(weather_router)
    app.include_router(graphql_app, prefix="/graphql")

    Instrumentator().instrument(app).expose(app)

    @app.on_event("startup")
    async def startup():
        await get_pool()

    @app.on_event("shutdown")
    async def shutdown():
        await close_pool()

    return app

app = create_app()