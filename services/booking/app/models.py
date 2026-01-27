from datetime import datetime
from pydantic import BaseModel


class BookingCreate(BaseModel):
    car_id: int
    borrower_user_id: int   # later: derive from JWT
    tenant_id: int
    start_time: datetime
    end_time: datetime


class Booking(BaseModel):
    id: int
    car_id: int
    borrower_user_id: int
    tenant_id: int
    start_time: datetime
    end_time: datetime
    status: str