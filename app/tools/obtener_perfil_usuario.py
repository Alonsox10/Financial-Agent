from __future__ import annotations

from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from psycopg.rows import class_row

from app.db.models import PerfilCliente
from app.db.session import pool
from app.graph.state import FinancialAdvisorState


@tool
async def obtener_perfil_usuario(
    state: Annotated[FinancialAdvisorState, InjectedState],
) -> dict:
    """Devuelve los productos bancarios contratados y el scoring crediticio interno del usuario.

    Úsala cuando el usuario pregunte qué productos tiene contratados con el
    banco, o cuando necesites evaluar su scoring crediticio para saber si
    califica para un producto nuevo (ej. un préstamo o un aumento de línea).
    """
    user_id = state["user_id"]

    async with pool.connection() as conn:
        async with conn.cursor(row_factory=class_row(PerfilCliente)) as cur:
            await cur.execute(
                """
                SELECT id, user_id, scoring_crediticio, productos_contratados, segmento, updated_at
                FROM perfiles_cliente
                WHERE user_id = %s
                """,
                (user_id,),
            )
            perfil = await cur.fetchone()

    if perfil is None:
        return {"mensaje": "El usuario no tiene un perfil registrado."}

    return {
        "productos_contratados": perfil.productos_contratados,
        "scoring_crediticio": perfil.scoring_crediticio,
    }
