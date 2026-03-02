from fastapi import Body
from fastapi import APIRouter, HTTPException
from ..db import get_pool
from ..models import BookingCreate, Booking
from ..config import settings
from aiokafka import AIOKafkaProducer
import asyncio

router = APIRouter(prefix="/bookings", tags=["bookings"])

kafka_producer = None

async def get_kafka_producer():
    global kafka_producer
    if kafka_producer is None:
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers
        )
        await kafka_producer.start()
    return kafka_producer


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

        # Log event to booking_events (event sourcing)
        import json
        await conn.execute(
            """
            INSERT INTO booking_events (booking_id, tenant_id, event_type, event_data)
            VALUES ($1, $2, $3, $4)
            """,
            row["id"],
            row["tenant_id"],
            "booking_created",
            json.dumps({
                "car_id": row["car_id"],
                "borrower_user_id": row["borrower_user_id"],
                "start_time": str(row["start_time"]),
                "end_time": str(row["end_time"]),
                "status": row["status"]
            })
        )

    # Publish booking_created event to Kafka
    producer = await get_kafka_producer()
    import json
    await producer.send_and_wait(
        "booking_created",
        json.dumps({
            "booking_id": row["id"],
            "tenant_id": row["tenant_id"]
        }).encode("utf-8")
    )

    return Booking(**row)


@router.get("/", response_model=list[Booking])
async def list_bookings(tenant_id: int, car_id: int | None = None, borrower_user_id: int | None = None):
    pool = await get_pool()

@router.get("/events/replay/{booking_id}")
async def replay_booking_events(booking_id: int, tenant_id: int):
    """Replay all events for a booking (CQRS/event sourcing demo)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT event_type, event_data, created_at
            FROM booking_events
            WHERE booking_id=$1 AND tenant_id=$2
            ORDER BY created_at ASC
            """,
            booking_id, tenant_id
        )
    # For demo: just return the event log
    return [
        {
            "event_type": r["event_type"],
            "event_data": r["event_data"],
            "created_at": r["created_at"]
        }
        for r in rows
    ]
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
async def cancel_booking(booking_id: int, tenant_id: int, cancellation_reason: str = Body(None)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE bookings
            SET status='cancelled', cancellation_reason=$3
            WHERE id=$1 AND tenant_id=$2
            RETURNING id, car_id, borrower_user_id, tenant_id, start_time, end_time, status, cancellation_reason
            """,
            booking_id,
            tenant_id,
            cancellation_reason
        )
        if not row:
            raise HTTPException(status_code=404, detail="Booking not found")
    return Booking(**row)