from fastapi import Query

from fastapi import Body

from fastapi import APIRouter, HTTPException
from ..db import get_pool
from ..models import BookingCreate, Booking
from datetime import datetime

router = APIRouter()

@router.patch("/bookings/{booking_id}/cancel", tags=["bookings"])
async def cancel_booking(booking_id: int, payload: dict = Body(...)):
    reason = payload.get("cancellation_reason")
    if not reason:
        raise HTTPException(status_code=400, detail="Cancellation reason required")
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE bookings SET status='cancelled', cancellation_reason=$1, updated_at=NOW()
            WHERE id=$2
            """,
            reason, booking_id
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Booking not found")
    return {"status": "cancelled", "booking_id": booking_id, "cancellation_reason": reason}



@router.get("/bookings", response_model=list[Booking], tags=["bookings"])
async def get_bookings(tenant_id: int = None, borrower_user_id: int = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if tenant_id is not None and borrower_user_id is not None:
            rows = await conn.fetch("SELECT * FROM bookings WHERE tenant_id=$1 AND borrower_user_id=$2 ORDER BY start_time DESC", tenant_id, borrower_user_id)
        elif tenant_id is not None:
            rows = await conn.fetch("SELECT * FROM bookings WHERE tenant_id=$1 ORDER BY start_time DESC", tenant_id)
        elif borrower_user_id is not None:
            rows = await conn.fetch("SELECT * FROM bookings WHERE borrower_user_id=$1 ORDER BY start_time DESC", borrower_user_id)
        else:
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

# List bookings for cars owned by the current user (car owner)
@router.get("/bookings/owner", response_model=list[Booking], tags=["bookings"])
async def get_owner_bookings(tenant_id: int = Query(...), owner_user_id: int = Query(...)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT b.* FROM bookings b
            JOIN cars c ON b.car_id = c.id
            WHERE c.tenant_id=$1 AND c.owner_user_id=$2
            ORDER BY b.start_time DESC
            """,
            tenant_id, owner_user_id
        )
    return [Booking(**dict(r)) for r in rows]

# Confirm a booking (set status to confirmed)
@router.patch("/bookings/{booking_id}/confirm", tags=["bookings"])
async def confirm_booking(booking_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE bookings SET status='confirmed', updated_at=NOW()
            WHERE id=$1 AND status='requested'
            """,
            booking_id
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Booking not found or not in requested state")
    return {"status": "confirmed", "booking_id": booking_id}

# Deny a booking (set status to denied)
@router.patch("/bookings/{booking_id}/deny", tags=["bookings"])
async def deny_booking(booking_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE bookings SET status='denied', updated_at=NOW()
            WHERE id=$1 AND status='requested'
            """,
            booking_id
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Booking not found or not in requested state")
    return {"status": "denied", "booking_id": booking_id}