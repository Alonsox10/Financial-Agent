from __future__ import annotations

from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from psycopg.rows import class_row

from app.db.models import Movimiento
from app.db.session import pool
from app.graph.state import FinancialAdvisorState


@tool
async def historial_movimientos(
    state: Annotated[FinancialAdvisorState, InjectedState],
    limite: int = 10,
) -> list[dict] | dict:
    """Devuelve las transacciones más recientes de las cuentas del usuario, con fecha, monto y descripción.

    Úsala cuando el usuario pregunte por sus últimos movimientos, gastos,
    consumos o transacciones recientes.

    Args:
        limite: cantidad máxima de movimientos a devolver (por defecto 10).
    """
    user_id = state["user_id"]
    limite = min(max(limite, 1), 50)

    async with pool.connection() as conn:
        async with conn.cursor(row_factory=class_row(Movimiento)) as cur:
            await cur.execute(
                """
                SELECT m.id, m.cuenta_id, m.fecha, m.monto, m.descripcion, m.tipo
                FROM movimientos m
                JOIN cuentas c ON c.id = m.cuenta_id
                WHERE c.user_id = %s
                ORDER BY m.fecha DESC
                LIMIT %s
                """,
                (user_id, limite),
            )
            movimientos = await cur.fetchall()

    if not movimientos:
        return {"mensaje": "El usuario no tiene movimientos registrados."}

    return [
        {
            "fecha": movimiento.fecha.isoformat(),
            "monto": str(movimiento.monto),
            "descripcion": movimiento.descripcion,
            "tipo": movimiento.tipo,
        }
        for movimiento in movimientos
    ]
