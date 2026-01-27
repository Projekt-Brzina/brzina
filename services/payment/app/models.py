from datetime import datetime
from pydantic import BaseModel


class PaymentCreate(BaseModel):
    booking_id: int
    tenant_id: int


class Payment(BaseModel):
    id: int
    booking_id: int
    tenant_id: int
    amount: int
    status: str
    mock_ref: str | None = None
    created_at: datetime