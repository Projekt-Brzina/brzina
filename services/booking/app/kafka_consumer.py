import asyncio
import json
from aiokafka import AIOKafkaConsumer
from .config import settings
from .db import get_pool

async def handle_payment_completed(event):
    data = json.loads(event.value)
    booking_id = data["booking_id"]
    tenant_id = data["tenant_id"]
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE bookings
            SET payment_status = 'paid', updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2
            """,
            booking_id, tenant_id
        )

async def consume_payment_completed():
    consumer = AIOKafkaConsumer(
        "payment_completed",
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="booking-service"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            await handle_payment_completed(msg)
    finally:
        await consumer.stop()

def start_payment_consumer_loop():
    loop = asyncio.get_event_loop()
    loop.create_task(consume_payment_completed())
