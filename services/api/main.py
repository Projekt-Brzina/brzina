from fastapi import FastAPI
import os
import asyncpg

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/health")
async def health():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}