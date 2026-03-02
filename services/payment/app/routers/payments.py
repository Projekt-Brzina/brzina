from fastapi import APIRouter, HTTPException
from ..db import get_pool
from ..models import PaymentCreate, Payment
from ..kafka_producer import send_payment_completed_event

router = APIRouter(prefix="/payments", tags=["payments"])



@router.post("/", response_model=Payment)
async def create_payment(payload: PaymentCreate):
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Join booking -> car to compute price
        booking = await conn.fetchrow(
            """
            SELECT b.id, b.tenant_id, b.start_time, b.end_time,
                   c.hourly_rate
            FROM bookings b
            JOIN cars c ON c.id = b.car_id
            WHERE b.id=$1 AND b.tenant_id=$2
            """,
            payload.booking_id,
            payload.tenant_id,
        )

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # Compute price (ceil hours)
        duration_seconds = (booking["end_time"] - booking["start_time"]).total_seconds()
        hours = int((duration_seconds + 3599) // 3600)
        if hours <= 0:
            hours = 1
        amount = hours * booking["hourly_rate"]

        row = await conn.fetchrow(
            """
            INSERT INTO payments (booking_id, tenant_id, amount, status, mock_ref)
            VALUES ($1, $2, $3, 'success', 'mock-payment')
            RETURNING id, booking_id, tenant_id, amount, status, mock_ref, created_at
            """,
            payload.booking_id,
            payload.tenant_id,
            amount,
        )

    # Emit payment_completed event
    await send_payment_completed_event(payload.booking_id, payload.tenant_id, amount)

    return Payment(**row)


@router.get("/", response_model=list[Payment])
async def list_payments(tenant_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, booking_id, tenant_id, amount, status, mock_ref, created_at
            FROM payments
            WHERE tenant_id=$1
            ORDER BY created_at DESC
            """,
            tenant_id,
        )
    return [Payment(**r) for r in rows]