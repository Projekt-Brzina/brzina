from fastapi import APIRouter
from ..db import get_pool

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}