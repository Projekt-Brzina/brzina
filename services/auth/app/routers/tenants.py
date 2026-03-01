from fastapi import APIRouter, HTTPException
from ..db import get_pool
from ..models import Tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.get("/", response_model=list[Tenant])
async def list_tenants():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, slug FROM tenants ORDER BY id")
    return [Tenant(**dict(r)) for r in rows]
