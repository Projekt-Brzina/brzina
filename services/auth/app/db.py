import asyncpg
from .config import settings

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(str(settings.database_url))
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None