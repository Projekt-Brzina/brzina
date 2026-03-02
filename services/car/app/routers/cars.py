
from fastapi import Body

from fastapi import APIRouter, HTTPException
from ..db import get_pool
from ..models import CarCreate, Car


from fastapi import Header
router = APIRouter(prefix="/cars", tags=["cars"])

@router.post("", response_model=Car)
@router.post("/", response_model=Car)
async def create_car(car: CarCreate, user_id: int = None, x_user_id: int = Header(None)):
    # Prefer user_id from query, else from x-user-id header, else default to 1
    resolved_user_id = user_id if user_id is not None else (x_user_id if x_user_id is not None else 1)
    print(f"[DEBUG] POST /cars - car: {car}, user_id: {resolved_user_id}")
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO cars (brand, model, plate, hourly_rate, year, color, description, owner_user_id, tenant_id, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
            RETURNING id, brand, model, plate, hourly_rate, year, color, description, owner_user_id, tenant_id, status, created_at, updated_at
            """,
            car.brand, car.model, car.plate, car.hourly_rate, car.year, car.color, car.description, resolved_user_id, car.tenant_id, car.status
        )
    return Car(**row)

@router.get("/", response_model=list[Car])
@router.get("", response_model=list[Car])
async def list_cars(tenant_id: int):
    print(f"[DEBUG] GET /cars - tenant_id: {tenant_id}")
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, brand, model, plate, hourly_rate, year, color, description, owner_user_id, tenant_id, status, created_at, updated_at
            FROM cars
            WHERE tenant_id=$1
            """,
            tenant_id
        )
    return [Car(**r) for r in rows]


# DELETE endpoint to remove a car
@router.delete("/{car_id}")
async def delete_car(car_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM cars WHERE id=$1
            """,
            car_id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Car not found")
    return {"id": car_id, "deleted": True}
# PATCH endpoint to update car status (active/inactive)
@router.patch("/{car_id}")
async def patch_car_status(car_id: int, status: str = Body(..., embed=True)):
    if status not in ("active", "inactive"):
        raise HTTPException(status_code=400, detail="Invalid status value")
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE cars SET status=$1, updated_at=NOW() WHERE id=$2 RETURNING id
            """,
            status, car_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"id": car_id, "status": status}

@router.get("/my", response_model=list[Car])
async def list_my_cars(tenant_id: int, user_id: int = None, x_user_id: int = Header(None)):
    # Debug: print all incoming headers
    import inspect
    from fastapi import Request as FastAPIRequest
    frame = inspect.currentframe()
    req = None
    while frame:
        if 'request' in frame.f_locals and isinstance(frame.f_locals['request'], FastAPIRequest):
            req = frame.f_locals['request']
            break
        frame = frame.f_back
    if req:
        print("[DEBUG] /cars/my incoming headers:", dict(req.headers))
    # Prefer user_id from query, else from x-user-id header, else default to 1
    resolved_user_id = user_id if user_id is not None else (x_user_id if x_user_id is not None else 1)
    print(f"[DEBUG] GET /cars/my - tenant_id: {tenant_id}, user_id: {resolved_user_id}")
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, brand, model, plate, hourly_rate, year, color, description, owner_user_id, tenant_id, status, created_at, updated_at
            FROM cars
            WHERE tenant_id=$1 AND owner_user_id=$2
            """,
            tenant_id, resolved_user_id
        )
    return [Car(**r) for r in rows]