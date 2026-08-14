from __future__ import annotations

from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from psycopg.rows import class_row

from app.db.models import Cuenta
from app.db.session import pool
from app.graph.state import FinancialAdvisorState


@tool
async def consultar_saldo(
    state: Annotated[FinancialAdvisorState, InjectedState],
) -> list[dict] | dict:
    """Consulta el saldo disponible y el saldo bloqueado de todas las cuentas bancarias del usuario.

    Úsala cuando el usuario pregunte cuánto dinero tiene, cuál es su saldo,
    o si puede cubrir un gasto con el dinero que tiene disponible (sin contar
    montos bloqueados, por ejemplo por una transferencia en proceso).
    """
    user_id = state["user_id"]

    async with pool.connection() as conn:
        async with conn.cursor(row_factory=class_row(Cuenta)) as cur:
            await cur.execute(
                """
                SELECT id, user_id, tipo_cuenta, saldo_disponible, saldo_bloqueado, moneda, created_at
                FROM cuentas
                WHERE user_id = %s
                """,
                (user_id,),
            )
            cuentas = await cur.fetchall()

    if not cuentas:
        return {"mensaje": "El usuario no tiene cuentas registradas."}

    return [
        {
            "tipo_cuenta": cuenta.tipo_cuenta,
            "saldo_disponible": str(cuenta.saldo_disponible),
            "saldo_bloqueado": str(cuenta.saldo_bloqueado),
            "moneda": cuenta.moneda,
        }
        for cuenta in cuentas
    ]
