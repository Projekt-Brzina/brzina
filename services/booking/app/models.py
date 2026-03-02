from datetime import datetime
from pydantic import BaseModel



class BookingCreate(BaseModel):
    car_id: int
    borrower_user_id: int   # later: derive from JWT
    tenant_id: int
    start_time: datetime
    end_time: datetime
    total_cost: float = None
    payment_status: str = None
    cancellation_reason: str = None



from typing import Union

class Booking(BaseModel):
    id: int
    car_id: int
    borrower_user_id: int
    tenant_id: int
    start_time: datetime
    end_time: datetime
    total_cost: float = None
    status: str
    payment_status: str = None
    cancellation_reason: str = None
    created_at: Union[str, datetime, None] = None
    updated_at: Union[str, datetime, None] = None