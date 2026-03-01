from datetime import datetime
from pydantic import BaseModel




class CarCreate(BaseModel):
    brand: str
    model: str
    plate: str
    hourly_rate: float
    year: int = None
    color: str = None
    description: str = None
    tenant_id: int




class Car(BaseModel):
    id: int
    brand: str
    model: str
    plate: str
    hourly_rate: float
    year: int = None
    color: str = None
    description: str = None
    owner_user_id: int
    tenant_id: int
    created_at: datetime = None
    updated_at: datetime = None