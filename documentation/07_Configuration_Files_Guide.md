# Configuration Files Guide
## Smart Retail Assistant
### Left Shift Program 2026 – Data & AI (T5)

---

## 1. Environment Configuration (`.env`)

Copy `.env.example` to `.env` and fill in your values:

```bash
# Azure OpenAI (optional – mock responses used if not set)
AZURE_OPENAI_API_KEY=sk-...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Database (SQLite for dev, Azure SQL for prod)
DATABASE_URL=sqlite+aiosqlite:///./data/retail.db
# Production:
# DATABASE_URL=mssql+pyodbc://user:pass@server.database.windows.net/db?driver=ODBC+Driver+18+for+SQL+Server

# App settings
APP_ENV=development
LOG_LEVEL=INFO
SECRET_KEY=change-me-in-production-use-32-char-random-string
```

---

## 2. Docker Configuration

### `Dockerfile`
Multi-stage build:
- **Stage 1 (builder):** Python 3.11-slim + build tools, installs all packages
- **Stage 2 (runtime):** Python 3.11-slim, copies only installed packages + app code

Key settings:
```dockerfile
EXPOSE 8000
CMD ["sh", "-c", "python pipeline/run_pipeline.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### `docker-compose.yml`
For local development with Docker:
```bash
docker-compose up --build
```
Mounts volumes for data persistence: `retail_data`, `retail_models`, `retail_vectorstore`

---

## 3. GitHub Actions (`.github/workflows/ci.yml`)

Three jobs:
1. **test** — runs on every push/PR: install deps → run pipeline → pytest
2. **docker-build** — runs on main only: build + push to ACR
3. **deploy** — runs on main only: deploy to Azure Web App

Required secrets: `ACR_LOGIN_SERVER`, `ACR_USERNAME`, `ACR_PASSWORD`, `AZURE_WEBAPP_NAME`, `AZURE_WEBAPP_PUBLISH_PROFILE`

---

## 4. Pytest Configuration (`pytest.ini`)

```ini
[pytest]
asyncio_mode = auto        # All async tests run automatically
testpaths = tests          # Only look in tests/ folder
log_cli = true             # Show logs during test run
log_cli_level = WARNING    # Only show warnings and above
```

---

## 5. Python Dependencies (`requirements.txt`)

Key packages and their purpose:

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.111.0 | Web framework |
| `uvicorn[standard]` | 0.29.0 | ASGI server |
| `sqlalchemy` | 2.0.30 | ORM (async) |
| `aiosqlite` | 0.20.0 | Async SQLite driver |
| `scikit-learn` | 1.4.2 | ML models (RF, IsoForest) |
| `pandas` | 2.2.2 | Data manipulation |
| `numpy` | 1.26.4 | Numerical computing |
| `joblib` | 1.4.2 | Model serialisation |
| `pyarrow` | 16.0.0 | Parquet file I/O |
| `langchain` | 0.2.1 | Agent framework |
| `langchain-openai` | 0.1.8 | Azure OpenAI integration |
| `faiss-cpu` | 1.8.0 | Vector similarity search |
| `openai` | 1.30.1 | OpenAI Python SDK |
| `fpdf2` | 2.7.9 | PDF generation |
| `pypdf` | 4.2.0 | PDF text extraction |
| `pydantic-settings` | 2.2.1 | Settings from env vars |
| `pytest-asyncio` | 0.23.6 | Async test support |

---

## 6. Project Structure Reference

```
Smart Retail Assistant/
│
├── app/                        # FastAPI application
│   ├── main.py                 # Entry point, route registration
│   ├── api/                    # REST endpoint handlers
│   │   ├── ingest.py           # POST /api/ingest
│   │   ├── predict.py          # GET  /api/predict
│   │   ├── search.py           # GET  /api/search
│   │   ├── agent.py            # POST /api/agent
│   │   ├── anomaly.py          # POST /api/anomaly
│   │   └── dashboard.py        # GET  /api/dashboard
│   ├── agents/                 # Multi-agent system
│   │   ├── orchestrator.py     # Intent routing
│   │   ├── demand_agent.py     # Demand forecasting agent
│   │   ├── qa_agent.py         # Customer Q&A RAG agent
│   │   └── anomaly_agent.py    # Anomaly detection agent
│   ├── ml/                     # ML model wrappers
│   │   ├── forecaster.py       # Random Forest demand forecast
│   │   └── anomaly_detector.py # Isolation Forest anomaly detection
│   ├── rag/                    # RAG system
│   │   ├── embeddings.py       # FAISS / TF-IDF vector store
│   │   └── retriever.py        # Document retrieval
│   ├── db/                     # Database layer
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   └── models.py           # ORM table definitions
│   └── core/                   # Shared utilities
│       ├── config.py           # Settings (pydantic-settings)
│       └── logging_config.py   # Structured logging
│
├── pipeline/                   # Data engineering pipeline
│   ├── ingest.py               # Raw data generation
│   ├── transform.py            # Stage + curate transformations
│   ├── train_forecast.py       # Train demand model
│   ├── train_anomaly.py        # Train anomaly model
│   ├── build_vectorstore.py    # Build RAG index (text fallback)
│   └── run_pipeline.py         # Full pipeline orchestrator
│
├── scripts/                    # Standalone utility scripts
│   ├── generate_dataset.py     # Generate all CSV datasets
│   ├── create_pdf_docs.py      # Create 8 PDF knowledge base docs
│   └── build_rag_from_pdfs.py  # Build RAG from PDFs
│
├── data/                       # Data layers (generated)
│   ├── raw/                    # CSV files from ingest
│   ├── staged/                 # Cleaned Parquet
│   └── curated/                # Feature-engineered Parquet
│
├── docs/                       # Knowledge base PDFs (generated)
├── ml_models/                  # Trained model .pkl files (generated)
├── vectorstore/                # FAISS/TF-IDF index (generated)
│
├── frontend/
│   └── index.html              # Single-page dashboard UI
│
├── tests/                      # pytest test suite
│   ├── conftest.py             # Fixtures (DB setup, HTTP client)
│   ├── test_api.py             # API endpoint tests
│   ├── test_ml.py              # ML model unit tests
│   └── test_agents.py          # Agent unit tests
│
├── documentation/              # Project documentation
│   ├── 01_Technical_Documentation.md
│   ├── 02_Architecture_Diagram.md
│   ├── 03_Reflection_Note.md
│   ├── 04_Demo_Script.md
│   ├── 05_PowerBI_Dashboard_Guide.md
│   ├── 06_Azure_Deployment_Guide.md
│   └── 07_Configuration_Files_Guide.md
│
├── .github/workflows/ci.yml    # GitHub Actions CI/CD
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Local Docker Compose
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
├── setup_and_run.bat           # One-click Windows setup script
└── README.md                   # Project overview
```
