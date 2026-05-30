"""
Smart Retail Assistant – FastAPI Application Entry Point
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

from app.core.logging_config import setup_logging
from app.db.database import init_db
from app.api import ingest, predict, search, agent, anomaly, dashboard

# Setup logging before anything else
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Smart Retail Assistant...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down Smart Retail Assistant")


app = FastAPI(
    title="Smart Retail Assistant",
    description="""
## Multi-Agent AI Platform for Smart Retail

An end-to-end platform integrating **Demand Forecasting**, **Customer Q&A (RAG)**, and **Anomaly Detection**.

### Agents
| Agent | Trigger keywords | Description |
|---|---|---|
| `DemandForecastAgent` | forecast, demand, predict, stock, reorder | ML-powered demand forecasting |
| `CustomerQAAgent` | (default) | RAG over 8 PDF knowledge base documents |
| `AnomalyDetectionAgent` | anomaly, spike, unusual, alert | Isolation Forest anomaly detection |

### Quick test
1. `GET /api/predict?product_id=P001&days=7` – demand forecast
2. `POST /api/agent` – chat with the multi-agent system
3. `POST /api/anomaly` – detect sales anomalies
4. `GET /api/dashboard` – aggregated metrics
    """,
    version="1.0.0",
    lifespan=lifespan,
    # Disable auto-generated docs so we can serve them manually
    # (prevents StaticFiles from blocking /docs)
    docs_url=None,
    redoc_url=None,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ─────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


# ── API routes ───────────────────────────────────────────────────
app.include_router(ingest.router,    prefix="/api", tags=["📥 Data Ingestion"])
app.include_router(predict.router,   prefix="/api", tags=["📈 Demand Forecasting"])
app.include_router(search.router,    prefix="/api", tags=["🔍 Document Search"])
app.include_router(agent.router,     prefix="/api", tags=["🤖 Multi-Agent"])
app.include_router(anomaly.router,   prefix="/api", tags=["🚨 Anomaly Detection"])
app.include_router(dashboard.router, prefix="/api", tags=["📊 Dashboard"])


# ── Health ───────────────────────────────────────────────────────
@app.get("/health", tags=["⚙️ System"], summary="Health check")
async def health_check():
    """Returns service status."""
    return {"status": "ok", "service": "Smart Retail Assistant", "version": "1.0.0"}


# ── Swagger UI (manually served so StaticFiles doesn't block it) ─
@app.get("/docs", include_in_schema=False)
async def swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Smart Retail Assistant – API Docs",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


@app.get("/docs/oauth2-redirect", include_in_schema=False)
async def swagger_oauth2_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_ui():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Smart Retail Assistant – ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


# ── Root redirect → dashboard UI ────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/ui/")


# ── Frontend static files (mounted at /ui to keep /docs free) ───
if os.path.exists("frontend"):
    app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")
