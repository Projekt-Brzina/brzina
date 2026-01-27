from fastapi import APIRouter, HTTPException
from ..db import get_pool
from ..models import CarCreate, Car

router = APIRouter(prefix="/cars", tags=["cars"])


@router.post("/", response_model=Car)
async def create_car(car: CarCreate, user_id: int = 1):
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO cars (brand, model, plate, hourly_rate, owner_user_id, tenant_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, brand, model, plate, hourly_rate, owner_user_id, tenant_id
            """,
            car.brand, car.model, car.plate, car.hourly_rate, user_id, car.tenant_id
        )

    return Car(**row)


@router.get("/", response_model=list[Car])
async def list_cars(tenant_id: int):
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

    return [Car(**r) for r in rows]