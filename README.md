# Smart Retail Assistant
## Left Shift Program 2026 – Data & AI (T5) Capstone Project

An end-to-end **Multi-Agent AI Platform** for retail:

| Capability | Technology |
|---|---|
| Demand Forecasting | Random Forest (scikit-learn) |
| Customer Q&A | RAG + FAISS + Azure OpenAI |
| Anomaly Detection | Isolation Forest (scikit-learn) |
| Backend | FastAPI + SQLAlchemy (async) |
| Data Pipeline | Pandas + Parquet (Raw → Staged → Curated) |
| Deployment | Docker + GitHub Actions + Azure Container Apps |

---

## Quick Start

### Option A – One-click (Windows)
```
Double-click setup_and_run.bat
```

### Option B – Manual
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate dataset + PDFs + train models + build RAG
python pipeline/run_pipeline.py

# 3. Start server
uvicorn app.main:app --reload --port 8000

# 4. Open browser
http://localhost:8000
```

### Option C – Docker
```bash
docker-compose up --build
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ingest` | Ingest sales records |
| GET | `/api/predict` | Demand forecast for a product |
| GET | `/api/search` | Knowledge base search (RAG) |
| POST | `/api/agent` | Multi-agent chat |
| POST | `/api/anomaly` | Detect anomalies in sales data |
| GET | `/api/anomaly/alerts` | Retrieve stored anomaly alerts |
| GET | `/api/dashboard` | Aggregated dashboard metrics |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API documentation (Swagger) |

---

## Project Documentation

| Document | Description |
|---|---|
| [Technical Documentation](documentation/01_Technical_Documentation.md) | Architecture, APIs, ML models, DB schema, security |
| [Architecture Diagram](documentation/02_Architecture_Diagram.md) | Azure cloud diagram, component diagram, data flow |
| [Reflection Note](documentation/03_Reflection_Note.md) | Challenges, learnings, optimisations |
| [Demo Script](documentation/04_Demo_Script.md) | 8-minute walkthrough guide for presentation |
| [Power BI Dashboard Guide](documentation/05_PowerBI_Dashboard_Guide.md) | Dashboard pages, DAX measures, data sources |
| [Azure Deployment Guide](documentation/06_Azure_Deployment_Guide.md) | Step-by-step Azure deployment with CLI commands |
| [Configuration Files Guide](documentation/07_Configuration_Files_Guide.md) | All config files explained, project structure |

---

## Deliverables Checklist

| Deliverable | Status | Location |
|---|---|---|
| Technical Documentation | ✅ | `documentation/01_Technical_Documentation.md` |
| Working Code Repository | ✅ | This repository |
| Deployment Diagram | ✅ | `documentation/02_Architecture_Diagram.md` |
| Configuration Files | ✅ | `.env.example`, `Dockerfile`, `docker-compose.yml`, `ci.yml` |
| Power BI Report Guide | ✅ | `documentation/05_PowerBI_Dashboard_Guide.md` |
| Demo Script | ✅ | `documentation/04_Demo_Script.md` |
| Reflection Note | ✅ | `documentation/03_Reflection_Note.md` |

---

## Mandatory Components Checklist

| Component | Implementation | Status |
|---|---|---|
| Python FastAPI backend | `app/main.py` + `app/api/` | ✅ |
| 4+ REST APIs | 7 endpoints total | ✅ |
| Database integration | SQLite (Azure SQL compatible) | ✅ |
| Logging + error handling | `app/core/logging_config.py` + global handler | ✅ |
| Unit testing (pytest) | `tests/` – 25+ tests | ✅ |
| ML/DL model | Random Forest (demand) + Isolation Forest (anomaly) | ✅ |
| Clean data pipeline | Raw → Staged → Curated (Parquet) | ✅ |
| Feature engineering | Lag features, rolling averages, time features | ✅ |
| Model persistence | `ml_models/*.pkl` (joblib) | ✅ |
| 2–3 agent system | DemandAgent + QAAgent + AnomalyAgent | ✅ |
| Prompt engineering | System prompts in each agent | ✅ |
| Embeddings + vector store | FAISS (Azure) / TF-IDF (fallback) | ✅ |
| RAG | PDF knowledge base + retrieval | ✅ |
| Multi-agent orchestration | `app/agents/orchestrator.py` | ✅ |
| Azure OpenAI | Integrated with mock fallback | ✅ |
| Azure deployment | Docker + GitHub Actions + Container Apps | ✅ |
| Security | Key Vault, env vars, input validation | ✅ |
| Data engineering pipeline | `pipeline/` – 5 steps | ✅ |
| Power BI dashboard | Guide + DAX measures | ✅ |
| Frontend | `frontend/index.html` | ✅ |
| CI/CD | `.github/workflows/ci.yml` | ✅ |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Azure OpenAI (Optional)

The platform works fully without Azure OpenAI keys using:
- **Mock LLM responses** for all agents
- **TF-IDF cosine similarity** for document search

To enable Azure OpenAI, copy `.env.example` to `.env` and fill in your keys.
