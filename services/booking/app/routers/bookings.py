
from fastapi import APIRouter, HTTPException
from ..db import get_pool
from ..models import BookingCreate, Booking
from datetime import datetime

router = APIRouter()

@router.get("/bookings", response_model=list[Booking], tags=["bookings"])
async def get_bookings():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM bookings ORDER BY start_time DESC")
    return [Booking(**dict(r)) for r in rows]

@router.post("/bookings", response_model=Booking, tags=["bookings"])
async def create_booking(booking: BookingCreate):
    pool = await get_pool()
    # Double-booking prevention: check for overlap
    async with pool.acquire() as conn:
        overlap = await conn.fetchval(
            """
            SELECT 1 FROM bookings
            WHERE car_id=$1 AND tenant_id=$2
              AND status IN ('requested', 'confirmed')
              AND NOT (end_time <= $3 OR start_time >= $4)
            LIMIT 1
            """,
            booking.car_id, booking.tenant_id, booking.start_time, booking.end_time
        )
        if overlap:
            raise HTTPException(status_code=409, detail="Car is already booked for this time range.")

        # Calculate total_cost (mock: 10.0 per hour)
        duration_hours = (booking.end_time - booking.start_time).total_seconds() / 3600
        total_cost = round(duration_hours * 10.0, 2) if duration_hours > 0 else 0.0

        row = await conn.fetchrow(
            """
            INSERT INTO bookings (car_id, borrower_user_id, tenant_id, start_time, end_time, total_cost, status, payment_status, cancellation_reason, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
            RETURNING *
            """,
            booking.car_id, booking.borrower_user_id, booking.tenant_id, booking.start_time, booking.end_time,
            total_cost, 'requested', booking.payment_status, booking.cancellation_reason
        )
    return Booking(**dict(row))
