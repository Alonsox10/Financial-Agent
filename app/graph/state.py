from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class FinancialAdvisorState(TypedDict):
    user_id: int
    phone_number: str

    # add_messages acumula turnos (incluye tool calls/resultados) en vez de
    # sobreescribir el estado en cada paso del grafo — el historial de Redis
    # se carga acá como mensajes iniciales en enrich_context.
    messages: Annotated[list[BaseMessage], add_messages]

    perfil_usuario: dict | None
    action: dict | None




