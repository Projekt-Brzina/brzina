from fastapi import APIRouter
from ..db import get_pool
from ..models import User
from typing import List

router = APIRouter()

@router.get("/users", response_model=List[User])
async def list_users(tenant_id: int = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if tenant_id:
            rows = await conn.fetch("SELECT * FROM users WHERE tenant_id=$1 ORDER BY id", tenant_id)
        else:
            rows = await conn.fetch("SELECT * FROM users ORDER BY id")
    return [User(**dict(r)) for r in rows]
