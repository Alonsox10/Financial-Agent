# Agente Asesor Financiero con IA

Sistema conversacional de nivel empresarial para banca, construido con **LangGraph**, **pgvector**, **GPT-4.1 mini (OpenAI)** y desplegado en **WhatsApp** vía **Google Cloud**. El agente asesor es de cara al usuario (el cliente del banco lo activa directamente por WhatsApp) y corre en paralelo a un agente de detección de fraude invisible, coordinados por un orquestador (LangGraph Supervisor).

> Documentación completa y decisiones de diseño: [`maestro.md`](maestro.md). Diagrama interactivo: `arquitectura-multiagente.html`. Diseño de capas de código: `arquitectura-limpia.md`.

## Arquitectura

- **Orquestador (LangGraph Supervisor):** decide, por cada turno, si invoca solo al Agente Asesor o, si el mensaje implica una operación sensible (transferencia nueva o confirmación pendiente), invoca en paralelo al Agente Asesor y al Agente de Fraude.
- **Agente Asesor Financiero:** único LLM (GPT-4.1 mini) con tools, razona y decide qué tools llamar. Mantiene memoria de sesión en Redis y usa RAG sobre pgvector para consultar productos bancarios, tasas y FAQs.
- **Agente de Fraude:** evalúa cada operación sensible de forma independiente contra patrones de riesgo en pgvector y devuelve un veredicto (`APPROVE` / `REVIEW` / `BLOCK`) sin exponer su razonamiento interno al asesor.
- **Pipeline de analítica:** eventos publicados de forma fire-and-forget vía Pub/Sub, consumidos por un worker y almacenados en el esquema `analytics` de Cloud SQL.

## Stack

| Capa | Tecnología |
|---|---|
| LLM | GPT-4.1 mini (OpenAI) |
| Embeddings | text-embedding-3-small (1536 dims) |
| Orquestación | LangGraph StateGraph |
| API | FastAPI |
| RAG / vectores | pgvector en PostgreSQL |
| Memoria corta | Redis (TTL 1h) |
| Canal usuario | WhatsApp (Meta Cloud API) |
| Dev local | Docker Compose |
| Cloud | Google Cloud Run + Cloud SQL + Memorystore |
| CI/CD | Cloud Build → Artifact Registry → Cloud Run |

## Requisitos previos

**Herramientas locales:** Python 3.11+, Docker y Docker Compose, ngrok (para exponer el webhook en desarrollo).

**Cuentas y credenciales:** API key de OpenAI, cuenta de Meta for Developers con app de WhatsApp Business, acceso al proyecto de Google Cloud del equipo.

## Puesta en marcha local

1. Copiar `.env.example` a `.env` y completar las credenciales (OpenAI API key, tokens de Meta, etc.).
2. Levantar Postgres (con pgvector) y Redis:
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```
3. Cargar los documentos iniciales del banco y generar sus embeddings:
   ```bash
   python scripts/seed_bank_documents.py
   ```
4. Levantar la API local:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Exponer el webhook con ngrok y configurarlo en el panel de Meta (developers.facebook.com → tu app → WhatsApp → Configuration):
   ```bash
   ngrok http 8000
   ```

## Estructura del proyecto

```
agente-financiero/
├── app/
│   ├── main.py                # Instancia FastAPI, monta routers
│   ├── core/                  # Config y logging
│   ├── api/routes/whatsapp.py # GET (verify) y POST (webhook)
│   ├── graph/                 # LangGraph: state, graph, nodes
│   ├── tools/                 # Tools del agente (@tool)
│   ├── rag/                   # Embeddings + retrieval sobre bank_documents
│   ├── memory/                # Cliente Redis (memoria corta)
│   ├── db/                    # Modelos y migraciones (Alembic)
│   ├── schemas/                # Pydantic request/response
│   └── services/whatsapp_client.py
├── orchestrator/               # LangGraph Supervisor
├── fraud_agent/                 # Agente de detección de fraude
├── events/                      # Publisher/worker de analítica (Pub/Sub)
├── tests/
├── scripts/
├── docker/
├── .env.example
└── requirements.txt
```

## Tools del agente asesor

| Tool | Qué hace |
|---|---|
| `consultar_saldo()` | Saldo disponible y bloqueado de las cuentas del usuario |
| `historial_movimientos()` | Últimas N transacciones |
| `buscar_productos_banco()` | RAG en pgvector sobre productos, tasas y FAQs |
| `calcular_intereses()` | Cálculo local de intereses, cuotas y amortización |
| `ejecutar_transferencia()` | Programa/ejecuta una operación, requiere confirmación previa (`interrupt()`) |
| `obtener_perfil_usuario()` | Productos contratados, scoring crediticio interno |

## Despliegue

Desarrollo local con Docker Compose; despliegue a Google Cloud (Cloud Run + Cloud SQL + Memorystore + Secret Manager) solo cuando se necesita la URL pública para la demo. Ver [`maestro.md`](maestro.md#9-despliegue-en-google-cloud) para el detalle de servicios y costos estimados por fase.

## Documentación

Para el detalle completo de decisiones técnicas, modelo de datos, arquitectura multiagente y convenciones del equipo, ver [`maestro.md`](maestro.md) — es la fuente única de verdad del proyecto.
