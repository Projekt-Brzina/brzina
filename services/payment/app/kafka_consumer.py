import asyncio
import json
from aiokafka import AIOKafkaConsumer
from .config import settings
from .db import get_pool

async def handle_booking_created(event):
    data = json.loads(event.value)
    booking_id = data["booking_id"]
    tenant_id = data["tenant_id"]
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Check if payment already exists
        exists = await conn.fetchval(
            "SELECT 1 FROM payments WHERE booking_id=$1 AND tenant_id=$2",
            booking_id, tenant_id
        )
        if exists:
            return
        # Insert payment with mock data (amount=0, status=pending)
        await conn.execute(
            """
            INSERT INTO payments (booking_id, tenant_id, amount, status, mock_ref)
            VALUES ($1, $2, 0, 'pending', 'auto-kafka')
            """,
            booking_id, tenant_id
        )

async def consume_booking_created():
    consumer = AIOKafkaConsumer(
        "booking_created",
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="payment-service"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            await handle_booking_created(msg)
    finally:
        await consumer.stop()

def start_consumer_loop():
    loop = asyncio.get_event_loop()
    loop.create_task(consume_booking_created())
