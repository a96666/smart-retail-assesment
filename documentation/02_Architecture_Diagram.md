# Architecture & Deployment Diagram
## Smart Retail Assistant – Azure Cloud Architecture
### Left Shift Program 2026 – Data & AI (T5)

---

## 1. High-Level Azure Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AZURE CLOUD                                         │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    AZURE RESOURCE GROUP: rg-smart-retail             │    │
│  │                                                                       │    │
│  │  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐ │    │
│  │  │  Azure Container │    │  Azure OpenAI    │    │  Azure AI      │ │    │
│  │  │  App (Backend)   │───►│  Service         │    │  Search        │ │    │
│  │  │                  │    │  • GPT-4o        │    │  (optional)    │ │    │
│  │  │  FastAPI + Uvicorn│   │  • Ada-002 embed │    │                │ │    │
│  │  │  Port 8000       │    └──────────────────┘    └────────────────┘ │    │
│  │  └────────┬─────────┘                                                │    │
│  │           │                                                           │    │
│  │  ┌────────▼─────────┐    ┌──────────────────┐    ┌────────────────┐ │    │
│  │  │  Azure SQL DB    │    │  Azure Blob       │    │  Azure Key     │ │    │
│  │  │  (or SQLite      │    │  Storage          │    │  Vault         │ │    │
│  │  │   for dev)       │    │  • ML models      │    │  • API keys    │ │    │
│  │  │                  │    │  • Vector store   │    │  • DB creds    │ │    │
│  │  │  Tables:         │    │  • Parquet data   │    │                │ │    │
│  │  │  sales_records   │    └──────────────────┘    └────────────────┘ │    │
│  │  │  forecasts       │                                                │    │
│  │  │  anomaly_alerts  │    ┌──────────────────┐    ┌────────────────┐ │    │
│  │  │  conversations   │    │  Azure Data       │    │  Azure         │ │    │
│  │  └──────────────────┘    │  Factory          │    │  Databricks    │ │    │
│  │                          │  (Data ingestion) │    │  (PySpark      │ │    │
│  │                          └──────────────────┘    │   transforms)  │ │    │
│  │                                                   └────────────────┘ │    │
│  │  ┌──────────────────┐    ┌──────────────────┐                        │    │
│  │  │  Azure Container │    │  Azure Monitor   │                        │    │
│  │  │  Registry (ACR)  │    │  + App Insights  │                        │    │
│  │  │  Docker images   │    │  Logs & metrics  │                        │    │
│  │  └──────────────────┘    └──────────────────┘                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
         ▲                                        ▲
         │ HTTPS                                  │ Publish
┌────────┴────────┐                    ┌──────────┴──────────┐
│   End Users     │                    │   Power BI Service  │
│   (Browser)     │                    │   Dashboard         │
└─────────────────┘                    └─────────────────────┘
         ▲
         │ CI/CD
┌────────┴────────┐
│  GitHub Actions │
│  • Test         │
│  • Build image  │
│  • Push to ACR  │
│  • Deploy       │
└─────────────────┘
```

---

## 2. Application Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMART RETAIL ASSISTANT                        │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  PRESENTATION LAYER                      │    │
│  │                                                           │    │
│  │   frontend/index.html  (Single Page Application)         │    │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    │
│  │   │Dashboard │ │Forecast  │ │Anomaly   │ │AI Chat   │  │    │
│  │   │Tab       │ │Tab       │ │Tab       │ │Tab       │  │    │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │ REST API                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   API LAYER (FastAPI)                    │    │
│  │                                                           │    │
│  │  /ingest  /predict  /search  /agent  /anomaly  /dashboard│    │
│  └──────┬──────────┬──────────┬──────────┬──────────┬──────┘    │
│         │          │          │          │          │             │
│  ┌──────▼──┐ ┌─────▼───┐ ┌───▼────┐ ┌──▼──────┐ ┌▼──────────┐ │
│  │ Ingest  │ │Forecast │ │ RAG    │ │ Agent   │ │ Dashboard │ │
│  │ Service │ │ Service │ │ Search │ │ Orchest.│ │ Metrics   │ │
│  └──────┬──┘ └─────┬───┘ └───┬────┘ └──┬──────┘ └┬──────────┘ │
│         │          │          │          │          │             │
│  ┌──────▼──────────▼──────────▼──────────▼──────────▼──────────┐│
│  │                    BUSINESS LOGIC LAYER                      ││
│  │                                                               ││
│  │  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐  ││
│  │  │  Agent Layer    │  │   ML Layer   │  │   RAG Layer    │  ││
│  │  │                 │  │              │  │                │  ││
│  │  │ • Orchestrator  │  │ • Forecaster │  │ • Embeddings   │  ││
│  │  │ • DemandAgent   │  │ • AnomalyDet │  │ • Retriever    │  ││
│  │  │ • QAAgent       │  │              │  │ • Azure Search │  ││
│  │  │ • AnomalyAgent  │  │              │  │   / FAISS /    │  ││
│  │  └─────────────────┘  └──────────────┘  │   TF-IDF       │  ││
│  │                                          └────────────────┘  ││
│  └──────────────────────────────────────────────────────────────┘│
│                           │                                        │
│  ┌────────────────────────▼───────────────────────────────────┐  │
│  │                     DATA LAYER                              │  │
│  │                                                              │  │
│  │  SQLite/Azure SQL    Parquet Files    Azure AI Search  .pkl  │  │
│  │  (ORM: SQLAlchemy)   (data/*)         (vectorstore/)  (ml/)  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Engineering Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                  DATA ENGINEERING PIPELINE                       │
│                                                                   │
│  ┌──────────────┐                                                │
│  │  Data Source │  Synthetic retail data (180 days)              │
│  │  (CSV files) │  15 products × 5 stores × 180 days            │
│  └──────┬───────┘                                                │
│         │ pipeline/ingest.py                                      │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │  RAW LAYER   │  data/raw/sales_raw.csv                        │
│  │              │  ~162,000 transaction records                   │
│  └──────┬───────┘                                                │
│         │ pipeline/transform.py → stage_data()                   │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │ STAGED LAYER │  data/staged/sales_staged.parquet              │
│  │              │  • Null removal                                 │
│  │              │  • Negative quantity filter                     │
│  │              │  • Outlier capping (99th percentile × 3)       │
│  └──────┬───────┘                                                │
│         │ pipeline/transform.py → curate_data()                  │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │CURATED LAYER │  data/curated/sales_curated.parquet            │
│  │              │  • Lag features: lag_1, lag_2, lag_3, lag_7    │
│  │              │  • Rolling avg: 7-day, 30-day                  │
│  │              │  • Time features: DOW, month, week, weekend    │
│  └──────┬───────┘                                                │
│         │                                                         │
│    ┌────┴────┐                                                    │
│    │         │                                                    │
│    ▼         ▼                                                    │
│  ┌────────┐ ┌────────────┐                                       │
│  │Demand  │ │ Anomaly    │                                       │
│  │Model   │ │ Model      │                                       │
│  │(.pkl)  │ │ (.pkl)     │                                       │
│  └────────┘ └────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Multi-Agent Orchestration Flow

```
User Message
     │
     ▼
┌────────────────────────────────────────┐
│         AgentOrchestrator              │
│                                        │
│  Intent Classification (keywords)      │
│                                        │
│  "forecast/demand/predict/stock"  ──►  DemandForecastAgent
│  "anomaly/spike/unusual/alert"    ──►  AnomalyDetectionAgent
│  (default)                        ──►  CustomerQAAgent
└────────────────────────────────────────┘
          │              │              │
          ▼              ▼              ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │DemandForecast│ │AnomalyDetect │ │CustomerQA    │
  │Agent         │ │Agent         │ │Agent (RAG)   │
  │              │ │              │ │              │
  │1. Get history│ │1. Run IsoFor.│ │1. Retrieve   │
  │2. Run RF     │ │2. Flag anomal│ │   top-k docs │
  │3. Format ctx │ │3. Build ctx  │ │2. Format ctx │
  │4. LLM/mock   │ │4. LLM/mock   │ │3. LLM/mock   │
  └──────────────┘ └──────────────┘ └──────────────┘
          │              │              │
          └──────────────┴──────────────┘
                         │
                         ▼
              Structured JSON Response
              { agent, intent, response, data }
                         │
                         ▼
              Persisted to agent_conversations
```

---

## 5. CI/CD Pipeline

```
Developer Push
     │
     ▼
┌─────────────────────────────────────────┐
│           GitHub Actions                 │
│                                          │
│  Trigger: push to main / PR to main      │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  Job 1: test                     │   │
│  │  • Setup Python 3.11             │   │
│  │  • pip install -r requirements   │   │
│  │  • python pipeline/run_pipeline  │   │
│  │  • pytest tests/ -v              │   │
│  └──────────────┬───────────────────┘   │
│                 │ (on main only)         │
│  ┌──────────────▼───────────────────┐   │
│  │  Job 2: docker-build             │   │
│  │  • Docker Buildx setup           │   │
│  │  • Login to Azure ACR            │   │
│  │  • Build & push image            │   │
│  │    :latest + :sha                │   │
│  └──────────────┬───────────────────┘   │
│                 │                        │
│  ┌──────────────▼───────────────────┐   │
│  │  Job 3: deploy                   │   │
│  │  • Azure Web App deploy          │   │
│  │  • Uses publish profile secret   │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
     │
     ▼
Azure Container App (live)
http://smart-retail-assistant.azurecontainerapps.io
```

---

## 6. Azure Services Used

| Service | Purpose | Tier |
|---|---|---|
| Azure Container Apps | Host FastAPI backend | Consumption |
| Azure OpenAI | GPT-4o chat + Ada-002 embeddings | Standard |
| Azure AI Search | RAG vector store (retail-knowledge-base index) | Free / Basic |
| Azure SQL Database | Production database | Basic |
| Azure Blob Storage | ML models, parquet files, documents | LRS |
| Azure Key Vault | Secrets management | Standard |
| Azure Data Factory | Data ingestion pipeline | Pay-per-use |
| Azure Databricks | PySpark data transformation | Standard |
| Azure Container Registry | Docker image storage | Basic |
| Azure Monitor + App Insights | Logging and metrics | Pay-per-use |
| Power BI Service | Analytics dashboard | Pro |

---

## 7. Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                SECURITY LAYERS                       │
│                                                       │
│  Transport:  HTTPS / TLS 1.3 (Azure managed cert)   │
│  Auth:       Azure AD (production) / API key (dev)   │
│  Secrets:    Azure Key Vault (never in code/git)     │
│  DB:         Parameterised queries (SQLAlchemy ORM)  │
│  Input:      Pydantic validation on all endpoints    │
│  CORS:       Restricted to known origins (prod)      │
│  Errors:     Global handler – no stack trace leakage │
│  Container:  Non-root user, read-only filesystem     │
└─────────────────────────────────────────────────────┘
```
