from __future__ import annotations

import asyncio
import selectors
import sys

sys.path.append(".")

from app.db.session import close_pool, init_pool, pool  # noqa: E402


async def main() -> None:
    await init_pool()
    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT version();")
                row = await cur.fetchone()
                print(f"Postgres respondió: {row['version']}")
    finally:
        await close_pool()


if __name__ == "__main__":
    loop_factory = (
        (lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
        if sys.platform == "win32"
        else None
    )
    try:
        asyncio.run(main(), loop_factory=loop_factory)
    except Exception:
        print("La prueba de conexión falló. Revisa las variables de entorno en .env")
        sys.exit(1)
