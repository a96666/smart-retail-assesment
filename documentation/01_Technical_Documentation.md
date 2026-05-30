# Technical Documentation
## Smart Retail Assistant – Multi-Agent AI Platform
### Left Shift Program 2026 – Data & AI (T5)

---

## 1. Project Overview

The **Smart Retail Assistant** is an end-to-end Multi-Agent AI Platform built for the retail domain. It integrates demand forecasting, customer Q&A, and anomaly detection into a unified platform backed by a FastAPI backend, machine learning models, a RAG-powered knowledge base, and Azure cloud services.

**Domain:** Smart Retail Assistant  
**Capabilities:** Demand Forecasting + Customer Q&A + Anomaly Detection  
**Stack:** Python · FastAPI · scikit-learn · LangChain · FAISS · SQLite/Azure SQL · Azure OpenAI · Docker · GitHub Actions

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                                │
│          Browser (frontend/index.html – Single Page App)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend (app/)                         │
│                                                                  │
│  POST /api/ingest    – Sales data ingestion                      │
│  GET  /api/predict   – Demand forecast                           │
│  GET  /api/search    – Knowledge base search                     │
│  POST /api/agent     – Multi-agent chat                          │
│  POST /api/anomaly   – Anomaly detection                         │
│  GET  /api/anomaly/alerts – Stored alerts                        │
│  GET  /api/dashboard – Aggregated metrics                        │
│  GET  /health        – Health check                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼──────┐ ┌───────▼──────┐ ┌──────▼────────┐
│  Agent Layer   │ │   ML Layer   │ │   RAG Layer   │
│                │ │              │ │               │
│ Orchestrator   │ │ Forecaster   │ │ Embeddings    │
│ DemandAgent    │ │ (RF model)   │ │ (Azure Search)│
│ QAAgent        │ │ AnomalyDet.  │ │ Retriever     │
│ AnomalyAgent   │ │ (IsoForest)  │ │               │
└────────────────┘ └──────────────┘ └───────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼────────┐
│                    Data Layer                        │
│  PostgreSQL (Neon) / SQLite – ORM via SQLAlchemy     │
│  Parquet files – data/raw, staged, curated           │
│  Azure AI Search index – retail-knowledge-base       │
│  ML artifacts – ml_models/*.pkl                      │
└─────────────────────────────────────────────────────┘
```

---

## 3. Data Flow

```
Raw CSV (pipeline/ingest.py)
    │
    ▼
Staged Parquet – cleaned, validated (pipeline/transform.py)
    │
    ▼
Curated Parquet – feature-engineered with lag/rolling features
    │
    ├──► Train Demand Model (Random Forest) → ml_models/demand_model.pkl
    ├──► Train Anomaly Model (Isolation Forest) → ml_models/anomaly_model.pkl
    └──► Seed SQLite database (500 sample records)

PDF Docs (scripts/create_pdf_docs.py)
    │
    ▼
Text Chunks (scripts/build_rag_from_pdfs.py)
    │
    ├──► Azure AI Search index (primary – vector search)
    ├──► FAISS local index     (fallback – if Azure Search unavailable)
    └──► TF-IDF pickle         (fallback – no API key needed)
```

---

## 4. Module Descriptions

### 4.1 `app/core/`
| File | Purpose |
|---|---|
| `config.py` | Pydantic Settings – loads all env vars with defaults |
| `logging_config.py` | Structured logging setup (stdout, formatted) |

### 4.2 `app/db/`
| File | Purpose |
|---|---|
| `database.py` | SQLAlchemy async engine, session factory, `init_db()` |
| `models.py` | ORM models: SalesRecord, ForecastResult, AnomalyAlert, AgentConversation |

### 4.3 `app/ml/`
| File | Purpose |
|---|---|
| `forecaster.py` | Loads `demand_model.pkl`, builds lag features, returns 7-day forecast with CI |
| `anomaly_detector.py` | Loads `anomaly_model.pkl`, runs Isolation Forest, z-score fallback |

### 4.4 `app/rag/`
| File | Purpose |
|---|---|
| `embeddings.py` | Builds/loads FAISS (Azure OpenAI) or TF-IDF vector store |
| `retriever.py` | `retrieve(query, k)` – returns top-k docs with scores |

### 4.5 `app/agents/`
| File | Purpose |
|---|---|
| `orchestrator.py` | Keyword-based intent classifier, routes to correct agent |
| `demand_agent.py` | Calls forecaster, formats context, calls Azure OpenAI or mock LLM |
| `qa_agent.py` | RAG retrieval + Azure OpenAI or mock LLM for customer Q&A |
| `anomaly_agent.py` | Runs anomaly detection, generates natural language insight |

### 4.6 `app/api/`
| File | Endpoint | Method |
|---|---|---|
| `ingest.py` | `/api/ingest` | POST |
| `predict.py` | `/api/predict` | GET |
| `search.py` | `/api/search` | GET |
| `agent.py` | `/api/agent` | POST |
| `anomaly.py` | `/api/anomaly`, `/api/anomaly/alerts` | POST, GET |
| `dashboard.py` | `/api/dashboard` | GET |

### 4.7 `pipeline/`
| File | Purpose |
|---|---|
| `ingest.py` | Generates 162,000+ synthetic sales records across 180 days |
| `transform.py` | Stage (clean/validate) → Curate (lag features, rolling averages) |
| `train_forecast.py` | Trains Random Forest regressor on lag features |
| `train_anomaly.py` | Trains Isolation Forest with 2% contamination rate |
| `build_vectorstore.py` | Builds FAISS/TF-IDF index from knowledge base |
| `run_pipeline.py` | Orchestrates all steps end-to-end |

---

## 5. API Reference

### POST `/api/ingest`
Ingest sales records into the database.

**Request:**
```json
{
  "records": [
    {
      "product_id": "P001",
      "product_name": "Wireless Headphones",
      "category": "Electronics",
      "quantity": 25,
      "unit_price": 49.99,
      "sale_date": "2024-06-01",
      "store_id": "S001"
    }
  ]
}
```
**Response:** `{ "message": "Records ingested successfully", "inserted": 1 }`

---

### GET `/api/predict`
Generate demand forecast for a product.

**Query params:** `product_id` (required), `days` (1–30, default 7)

**Response:**
```json
{
  "product_id": "P001",
  "forecast_days": 7,
  "forecast": [
    { "date": "2024-06-02", "predicted_demand": 42.5, "lower": 31.2, "upper": 53.8 }
  ]
}
```

---

### GET `/api/search`
Semantic search over the retail knowledge base.

**Query params:** `q` (required), `k` (1–10, default 3)

**Response:**
```json
{
  "query": "return policy",
  "results": [
    { "content": "...", "source": "Return Policy", "score": 0.87 }
  ],
  "total": 3
}
```

---

### POST `/api/agent`
Send a message to the multi-agent system.

**Request:**
```json
{
  "message": "What is the demand forecast for P001?",
  "session_id": "optional-uuid",
  "context": { "product_id": "P001" }
}
```
**Response:**
```json
{
  "session_id": "uuid",
  "agent": "DemandForecastAgent",
  "intent": "demand",
  "response": "Based on the forecast...",
  "data": null
}
```

---

### POST `/api/anomaly`
Detect anomalies in sales records.

**Request:**
```json
{
  "records": [
    { "product_id": "P001", "date": "2024-06-01", "quantity": 250 }
  ]
}
```
**Response:**
```json
{
  "total_records": 1,
  "anomaly_count": 1,
  "anomalies": [...],
  "insight": "Anomaly Analysis Summary..."
}
```

---

### GET `/api/dashboard`
Returns aggregated metrics for the dashboard.

**Response fields:** `total_revenue_30d`, `total_transactions_30d`, `anomaly_count_7d`, `top_products`, `revenue_by_category`, `daily_revenue_trend`

---

## 6. ML Models

### 6.1 Demand Forecasting Model
- **Algorithm:** Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`)
- **Features:** `lag_1`, `lag_2`, `lag_3`, `lag_7` (previous day quantities)
- **Target:** `quantity` (daily units sold)
- **Train/Test split:** 80/20
- **Hyperparameters:** `n_estimators=100`, `max_depth=10`, `random_state=42`
- **Persistence:** `ml_models/demand_model.pkl` (joblib)
- **Fallback:** 7-day moving average if model file not found

### 6.2 Anomaly Detection Model
- **Algorithm:** Isolation Forest (`sklearn.ensemble.IsolationForest`)
- **Features:** `quantity` (univariate)
- **Contamination:** 2% (expected anomaly rate)
- **Hyperparameters:** `n_estimators=100`, `random_state=42`
- **Persistence:** `ml_models/anomaly_model.pkl` (joblib)
- **Fallback:** Z-score method (threshold=2.5) if model file not found

---

## 7. GenAI / RAG System

### 7.1 Vector Store
- **Primary:** Azure AI Search with Azure OpenAI `text-embedding-ada-002` embeddings (1536-dim HNSW index)
- **Fallback 1:** FAISS local index with Azure OpenAI embeddings (if `faiss-cpu` installed)
- **Fallback 2:** TF-IDF cosine similarity (no API key required)
- **Documents:** 8 PDF knowledge base documents, chunked at 400 chars with 80-char overlap
- **Index name:** `retail-knowledge-base` (configurable via `AZURE_SEARCH_INDEX_NAME`)
- **Index location (local fallbacks):** `vectorstore/`
- **Backend detection:** `vectorstore/backend.txt` records which backend was used at build time

### 7.2 Agent Prompts

**DemandForecastAgent system prompt:**
> "You are a Demand Forecasting Expert for a retail company. You have access to sales history and ML-generated demand forecasts. Your job is to interpret demand forecasts clearly, identify trends, recommend inventory levels and reorder points, and flag potential stockout or overstock risks."

**CustomerQAAgent system prompt:**
> "You are a helpful retail customer assistant. You answer questions about products, store policies, promotions, and services. Use ONLY the provided context to answer. If the answer is not in the context, say so politely."

**AnomalyDetectionAgent system prompt:**
> "You are a Retail Analytics Expert specializing in anomaly detection. You analyze sales anomalies and provide clear explanations, possible root causes, and recommended actions for the operations team."

### 7.3 Agent Orchestration
Intent is classified by keyword matching:
- **demand** keywords: forecast, demand, predict, sales, trend, inventory, stock, reorder
- **anomaly** keywords: anomaly, unusual, spike, drop, alert, outlier, abnormal
- **qa** (default): all other queries → CustomerQAAgent

---

## 8. Database Schema

### `sales_records`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| product_id | VARCHAR(50) | Product identifier |
| product_name | VARCHAR(200) | Product display name |
| category | VARCHAR(100) | Product category |
| quantity | INTEGER | Units sold |
| unit_price | FLOAT | Price per unit |
| total_revenue | FLOAT | quantity × unit_price |
| sale_date | DATETIME | Date of sale |
| store_id | VARCHAR(50) | Store identifier |
| created_at | DATETIME | Record creation timestamp |

### `forecast_results`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| product_id | VARCHAR(50) | Product identifier |
| forecast_date | DATETIME | Forecasted date |
| predicted_demand | FLOAT | Predicted units |
| confidence_lower | FLOAT | Lower bound (95% CI) |
| confidence_upper | FLOAT | Upper bound (95% CI) |

### `anomaly_alerts`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| product_id | VARCHAR(50) | Product identifier |
| sale_date | DATETIME | Date of anomalous sale |
| actual_quantity | FLOAT | Observed quantity |
| anomaly_score | FLOAT | Isolation Forest score |
| is_anomaly | BOOLEAN | True if flagged |
| description | TEXT | Natural language description |

### `agent_conversations`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| session_id | VARCHAR(100) | Chat session UUID |
| agent_type | VARCHAR(50) | Agent that responded |
| user_message | TEXT | User's input |
| agent_response | TEXT | Agent's response |

---

## 9. Security Considerations

- All secrets (API keys, DB credentials) stored in `.env` file, never committed to Git
- `.env` is in `.gitignore`; `.env.example` provided as template
- Azure Key Vault recommended for production secret management
- CORS configured (restrict origins in production)
- Input validation via Pydantic models on all endpoints
- SQL injection prevented by SQLAlchemy ORM (parameterised queries)
- Global exception handler prevents stack trace leakage

---

## 10. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `AZURE_OPENAI_API_KEY` | Optional | Azure OpenAI API key (mock used if absent) |
| `AZURE_OPENAI_ENDPOINT` | Optional | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Optional | Chat model deployment name (default: gpt-4o) |
| `AZURE_OPENAI_API_VERSION` | Optional | API version (default: 2024-02-01) |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Optional | Embedding model name (default: text-embedding-ada-002) |
| `AZURE_SEARCH_ENDPOINT` | Optional | Azure AI Search service endpoint |
| `AZURE_SEARCH_API_KEY` | Optional | Azure AI Search admin key |
| `AZURE_SEARCH_INDEX_NAME` | Optional | Search index name (default: retail-knowledge-base) |
| `AZURE_STORAGE_CONNECTION_STRING` | Optional | Azure Blob Storage connection string |
| `AZURE_BLOB_CONTAINER` | Optional | Blob container name (default: smart-retail-ai) |
| `DATABASE_URL` | Optional | SQLAlchemy DB URL (default: SQLite) |
| `APP_ENV` | Optional | development / production |
| `LOG_LEVEL` | Optional | INFO / DEBUG / WARNING |
