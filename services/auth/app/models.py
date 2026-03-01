from pydantic import BaseModel
from pydantic import EmailStr
# For tenant API
class Tenant(BaseModel):
    id: int
    name: str
    slug: str



class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str = None
    payment_info: str = None
    is_admin: bool = False
    tenant_id: int

# Optionally, add a User model for responses
class User(BaseModel):
    id: int
    email: EmailStr
    name: str = None
    payment_info: str = None
    is_admin: bool = False
    tenant_id: int
    is_active: bool = True
    created_at: str = None
    updated_at: str = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"