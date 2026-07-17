from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

load_dotenv()

logger = logging.getLogger("app.db")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "")
POSTGRES_USER = os.getenv("POSTGRES_USER", "")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

DB_POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "1"))
DB_POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "10"))

CONNINFO = (
    f"host={POSTGRES_HOST} port={POSTGRES_PORT} dbname={POSTGRES_DB} "
    f"user={POSTGRES_USER} password={POSTGRES_PASSWORD}"
)

pool = AsyncConnectionPool(
    conninfo=CONNINFO,
    min_size=DB_POOL_MIN_SIZE,
    max_size=DB_POOL_MAX_SIZE,
    kwargs={"row_factory": dict_row},
    open=False,
)


async def init_pool() -> None:
    logger.info(
        "Conectando a PostgreSQL en %s:%s/%s (pool min=%d max=%d)...",
        POSTGRES_HOST,
        POSTGRES_PORT,
        POSTGRES_DB,
        DB_POOL_MIN_SIZE,
        DB_POOL_MAX_SIZE,
    )
    try:
        await pool.open(wait=True, timeout=10)
    except Exception:
        logger.exception("No se pudo conectar a PostgreSQL")
        raise
    logger.info("Conexión a PostgreSQL establecida")


async def close_pool() -> None:
    logger.info("Cerrando pool de conexiones a PostgreSQL...")
    await pool.close()
    logger.info("Pool de conexiones cerrado")


async def get_connection():
    logger.debug("Tomando conexión del pool")
    async with pool.connection() as conn:
        try:
            yield conn
        finally:
            logger.debug("Conexión devuelta al pool")
