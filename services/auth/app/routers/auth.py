from typing import List
import jwt
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..db import get_pool
from ..security import hash_password, verify_password, create_access_token
from ..models import User, UserCreate, UserLogin, Token
from ..config import settings
from pydantic import BaseModel
from .tenants import router as tenants_router

router = APIRouter(prefix="/auth", tags=["auth"])

# For profile update
class UserUpdate(BaseModel):
    name: str = None
    payment_info: str = None

security = HTTPBearer()

def get_jwt_payload(request: Request):
    auth = request.headers.get("authorization")
    if not auth:
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except Exception:
        return None


@router.put("/me")
async def update_me(update: UserUpdate, request: Request):
    payload = get_jwt_payload(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or missing JWT")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET name=$1, payment_info=$2, updated_at=NOW() WHERE id=$3",
            update.name, update.payment_info, int(payload.get("sub"))
        )
    return {"status": "ok"}

@router.get("/me", response_model=User)
async def get_me(request: Request):
    payload = get_jwt_payload(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or missing JWT")
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id=$1", int(payload.get("sub"))
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
    return User(**dict(row))


@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    pool = await get_pool()

    # Log password length and value (truncate for security)
    import logging
    logging.warning(f"Register password length: {len(user.password)}")
    logging.warning(f"Register password preview: {user.password[:10]}")

    # Truncate password to 72 chars for bcrypt
    password = user.password[:72]
    logging.warning(f"Truncated password length: {len(password)}")

    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email=$1 AND tenant_id=$2",
            user.email, user.tenant_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed = hash_password(password)


        row = await conn.fetchrow(
            """
            INSERT INTO users (email, password_hash, name, payment_info, is_admin, tenant_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            user.email, hashed, user.name, user.payment_info, user.is_admin, user.tenant_id
        )

    token = create_access_token(row["id"], user.tenant_id)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, password_hash, tenant_id FROM users WHERE email=$1",
            credentials.email
        )

        if not row or not verify_password(credentials.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(row["id"], row["tenant_id"])
    return Token(access_token=token)