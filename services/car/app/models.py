from pydantic import BaseModel


class CarCreate(BaseModel):
    brand: str
    model: str
    plate: str
    hourly_rate: int
    tenant_id: int


class Car(BaseModel):
    id: int
    brand: str
    model: str
    plate: str
    hourly_rate: int
    owner_user_id: int
    tenant_id: int