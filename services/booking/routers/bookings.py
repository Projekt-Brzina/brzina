from fastapi import APIRouter, HTTPException
from ..db import get_pool
from ..models import BookingCreate, Booking

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=Booking)
async def create_booking(payload: BookingCreate):
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Ensure car exists and belongs to the tenant
        car = await conn.fetchrow(
            "SELECT id, tenant_id FROM cars WHERE id=$1",
            payload.car_id,
        )
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        if car["tenant_id"] != payload.tenant_id:
            raise HTTPException(status_code=403, detail="Car does not belong to tenant")

        # Check overlapping bookings for this car
        overlap = await conn.fetchrow(
            """
            SELECT id FROM bookings
            WHERE car_id = $1
              AND tenant_id = $2
              AND status IN ('requested', 'confirmed')
              AND NOT (end_time <= $3 OR start_time >= $4)
            """,
            payload.car_id,
            payload.tenant_id,
            payload.start_time,
            payload.end_time,
        )
        if overlap:
            raise HTTPException(status_code=409, detail="Time slot already booked")

        row = await conn.fetchrow(
            """
            INSERT INTO bookings (car_id, borrower_user_id, tenant_id, start_time, end_time, status)
            VALUES ($1, $2, $3, $4, $5, 'requested')
            RETURNING id, car_id, borrower_user_id, tenant_id, start_time, end_time, status
            """,
            payload.car_id,
            payload.borrower_user_id,
            payload.tenant_id,
            payload.start_time,
            payload.end_time,
        )

    return Booking(**row)


@router.get("/", response_model=list[Booking])
async def list_bookings(tenant_id: int, car_id: int | None = None, borrower_user_id: int | None = None):
    pool = await get_pool()
    query = """
        SELECT id, car_id, borrower_user_id, tenant_id, start_time, end_time, status
        FROM bookings
        WHERE tenant_id=$1
    """
    params: list = [tenant_id]

    if car_id is not None:
        query += " AND car_id=$2"
        params.append(car_id)
    elif borrower_user_id is not None:
        query += " AND borrower_user_id=$2"
        params.append(borrower_user_id)

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [Booking(**r) for r in rows]


@router.patch("/{booking_id}/cancel", response_model=Booking)
async def cancel_booking(booking_id: int, tenant_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE bookings
            SET status='cancelled'
            WHERE id=$1 AND tenant_id=$2
            RETURNING id, car_id, borrower_user_id, tenant_id, start_time, end_time, status
            """,
            booking_id,
            tenant_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Booking not found")
    return Booking(**row)