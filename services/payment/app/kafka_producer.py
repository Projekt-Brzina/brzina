import json
from aiokafka import AIOKafkaProducer
from .config import settings
from decimal import Decimal

producer = None

def default_json(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

async def get_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=default_json).encode('utf-8')
        )
        await producer.start()
    return producer

async def send_payment_completed_event(booking_id, tenant_id, amount):
    prod = await get_producer()
    # Ensure amount is float for JSON serialization
    if isinstance(amount, Decimal):
        amount = float(amount)
    event = {
        "booking_id": booking_id,
        "tenant_id": tenant_id,
        "amount": amount,
        "event_type": "payment_completed"
    }
    await prod.send_and_wait("payment_completed", event)

async def close_producer():
    global producer
    if producer:
        await producer.stop()
        producer = None
