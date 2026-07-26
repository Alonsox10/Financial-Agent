from __future__ import annotations

import logging
from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.db.session import CONNINFO
from app.graph.state import FinancialAdvisorState

logger = logging.getLogger("app.graph")

_llm: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    # Instanciación perezosa: ChatOpenAI valida OPENAI_API_KEY al crearse, y
    # si esto corriera a nivel de módulo, cualquier `import` de este archivo
    # fallaría sin la key seteada (ej. al correr tests o el checkpointer solo).
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4.1-mini")
    return _llm


_checkpointer_cm = None
checkpointer: AsyncPostgresSaver | None = None


async def init_checkpointer() -> None:
    global _checkpointer_cm, checkpointer
    logger.info("Inicializando checkpointer de LangGraph en PostgreSQL...")
    _checkpointer_cm = AsyncPostgresSaver.from_conn_string(CONNINFO)
    checkpointer = await _checkpointer_cm.__aenter__()
    await checkpointer.setup()
    logger.info("Checkpointer listo")


async def close_checkpointer() -> None:
    if _checkpointer_cm is not None:
        logger.info("Cerrando checkpointer de LangGraph...")
        await _checkpointer_cm.__aexit__(None, None, None)
        logger.info("Checkpointer cerrado")


async def enrich_context(state: FinancialAdvisorState) -> dict:
    # TODO: cargar historial de Redis (app/memory/redis_client.py) y perfil
    # (obtener_perfil_usuario) cuando esas piezas existan.
    return {}


async def call_model(state: FinancialAdvisorState) -> dict:
    response = await _get_llm().ainvoke(state["messages"])
    return {"messages": [response]}


async def execute_tools(state: FinancialAdvisorState) -> dict:
    # TODO: reemplazar por ToolNode(tools) cuando existan las tools de la sección 7.
    return {}


async def respond(state: FinancialAdvisorState) -> dict:
    # TODO: acá se formatea y envía la respuesta final por WhatsApp.
    return {}


def route_after_model(state: FinancialAdvisorState) -> Literal["execute_tools", "respond"]:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "execute_tools"
    return "respond"


def build_graph() -> CompiledStateGraph:
    if checkpointer is None:
        raise RuntimeError("El checkpointer no está inicializado. Llama a init_checkpointer() primero.")

    graph = StateGraph(FinancialAdvisorState)
    graph.add_node("enrich_context", enrich_context)
    graph.add_node("call_model", call_model)
    graph.add_node("execute_tools", execute_tools)
    graph.add_node("respond", respond)

    graph.add_edge(START, "enrich_context")
    graph.add_edge("enrich_context", "call_model")
    graph.add_conditional_edges(
        "call_model",
        route_after_model,
        {"execute_tools": "execute_tools", "respond": "respond"},
    )
    graph.add_edge("execute_tools", "call_model")
    graph.add_edge("respond", END)

    return graph.compile(checkpointer=checkpointer)
