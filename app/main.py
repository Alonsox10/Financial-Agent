from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import close_pool, init_pool, pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="Agente Asesor Financiero", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT version();")
            row = await cur.fetchone()
    return {"status": "ok", "postgres_version": row["version"]}
