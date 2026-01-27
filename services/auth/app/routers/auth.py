from fastapi import APIRouter, HTTPException
from ..db import get_pool
from ..security import hash_password, verify_password, create_access_token
from ..models import UserCreate, UserLogin, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    pool = await get_pool()

    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email=$1 AND tenant_id=$2",
            user.email, user.tenant_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed = hash_password(user.password)

        row = await conn.fetchrow(
            """
            INSERT INTO users (email, password_hash, tenant_id)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            user.email, hashed, user.tenant_id
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