# Demo Script & Walkthrough Guide
## Smart Retail Assistant – 5–10 Minute Demo
### Left Shift Program 2026 – Data & AI (T5)

---

## Pre-Demo Checklist

Before starting the demo, ensure:
- [ ] `setup_and_run.bat` has been executed successfully
- [ ] Server is running at `http://localhost:8000`
- [ ] Browser is open at `http://localhost:8000`
- [ ] API docs are accessible at `http://localhost:8000/docs`
- [ ] Terminal is visible showing server logs

---

## Demo Flow (8 minutes)

---

### Segment 1 – Introduction (1 min)

> "This is the Smart Retail Assistant — a Multi-Agent AI Platform that helps retail businesses with three core capabilities: demand forecasting, customer Q&A, and anomaly detection. It's built with FastAPI, scikit-learn, LangChain, and Azure OpenAI, deployed on Azure Container Apps."

**Show:** The dashboard tab with metrics loaded.

**Point out:**
- Total revenue (30 days)
- Transaction count
- Anomaly alert count
- Top products table
- Revenue by category bar chart
- Daily revenue trend line chart

---

### Segment 2 – Data Pipeline (1 min)

> "The platform starts with a data engineering pipeline. It generates 162,000+ synthetic retail transactions across 180 days, 15 products, and 5 stores. The pipeline runs three stages:"

**Show:** Open `pipeline/` folder in the file explorer.

**Explain:**
1. `ingest.py` — Raw CSV generation (simulates Azure Data Factory)
2. `transform.py` — Stage (clean/validate) → Curate (lag features, rolling averages) → Parquet files
3. `train_forecast.py` — Trains Random Forest on lag features
4. `train_anomaly.py` — Trains Isolation Forest for anomaly detection

**Show:** `data/raw/`, `data/staged/`, `data/curated/` folders with files.

---

### Segment 3 – Demand Forecasting (1.5 min)

> "The first agent is the Demand Forecasting Agent. It uses a Random Forest model trained on lag features to predict product demand for the next 7 days."

**Action:** Click the **Demand Forecast** tab.

**Demo steps:**
1. Enter `P001` in the Product ID field
2. Set days to `7`
3. Click **Generate Forecast**
4. Show the forecast table with dates, predicted demand, and confidence intervals

> "Notice the confidence intervals — the model gives us a lower and upper bound, not just a point estimate. This helps the inventory team plan safety stock."

**Then:** Switch to the **AI Assistant** tab and type:
> `"What is the demand forecast for P001 and should I reorder?"`

Show the DemandForecastAgent responding with the forecast context and inventory recommendation.

---

### Segment 4 – Anomaly Detection (1.5 min)

> "The second agent is the Anomaly Detection Agent. It uses an Isolation Forest model to flag unusual sales patterns — spikes, drops, or stockouts."

**Action:** Click the **Anomaly Detection** tab.

**Demo steps:**
1. Click **Load Sample Data** — this loads 20 records with some injected spikes
2. Click **Detect Anomalies**
3. Show the results table with anomaly/normal tags and scores
4. Point to the AI insight section below the table

> "The agent doesn't just flag numbers — it generates a natural language explanation of what the anomaly means and what the operations team should do about it."

**Show:** The anomaly alerts in the table — red badges for anomalies, green for normal.

---

### Segment 5 – Customer Q&A (RAG) (2 min)

> "The third agent is the Customer Q&A Agent. It uses Retrieval-Augmented Generation — it searches our knowledge base of 8 PDF documents and uses that context to answer customer questions accurately."

**Action:** Click the **Knowledge Search** tab first.

**Demo steps:**
1. Type `return policy` and click Search
2. Show the retrieved documents with source names and relevance scores

> "These are chunks from our actual PDF documents — the return policy, delivery guide, loyalty programme, warranty guide, and more."

**Then:** Switch to the **AI Assistant** tab and ask:
> `"What is the return policy for electronics?"`

Show the CustomerQAAgent responding with accurate information from the knowledge base.

**Ask another question:**
> `"How do I earn loyalty points and what are the Gold member benefits?"`

Show the agent pulling from the loyalty programme document.

---

### Segment 6 – Multi-Agent Orchestration (1 min)

> "The orchestrator automatically routes queries to the right agent. Let me show you a few examples."

**In the AI Assistant tab, type these in sequence:**

1. `"Are there any unusual sales patterns I should know about?"` → routes to AnomalyDetectionAgent
2. `"What are your store opening hours?"` → routes to CustomerQAAgent
3. `"Show me the sales trend for product P003"` → routes to DemandForecastAgent

> "Notice the agent name shown above each response — the orchestrator classified the intent and picked the right specialist automatically."

---

### Segment 7 – API & Technical Stack (1 min)

> "The backend exposes 7 REST APIs. Let me show the interactive API documentation."

**Action:** Open `http://localhost:8000/docs` in a new tab.

**Show:**
- The Swagger UI with all endpoints grouped by tag
- Expand `POST /api/agent` and show the request/response schema
- Expand `GET /api/predict` and show the query parameters

> "All endpoints have full Pydantic validation, structured logging, and error handling. The system also has a full pytest test suite covering APIs, ML models, and agents."

---

### Segment 8 – Deployment (30 sec)

> "The platform is containerised with Docker and deployed via GitHub Actions CI/CD to Azure Container Apps. The pipeline runs tests, builds the Docker image, pushes to Azure Container Registry, and deploys automatically on every push to main."

**Show:** `.github/workflows/ci.yml` briefly.

**Show:** `Dockerfile` — point out the multi-stage build.

---

## Key Talking Points

- **No Azure key required** — the system works fully offline with mock LLM responses and TF-IDF search. Plug in Azure OpenAI keys for production-quality responses.
- **Fallback-first design** — every external dependency has a fallback, making the system resilient.
- **Production-ready patterns** — async DB, structured logging, input validation, global error handling, CI/CD.
- **Extensible** — adding a new agent is as simple as creating a new class and registering it in the orchestrator.

---

## Common Questions & Answers

**Q: How does the orchestrator decide which agent to use?**
A: Currently keyword-based intent classification. It can be upgraded to LLM-based classification using function calling for more nuanced routing.

**Q: What happens if Azure OpenAI is not configured?**
A: The system falls back to rule-based mock responses for agents and TF-IDF for search. The platform is fully functional without any API keys.

**Q: How accurate is the demand forecast?**
A: On the synthetic dataset, the Random Forest achieves MAE of ~3–5 units. In production, accuracy improves significantly with more historical data and additional features (promotions, weather, events).

**Q: Can this handle real-time data?**
A: The current architecture is batch-oriented. For real-time, Azure Event Hub + Data Activator would be added to stream sales events and trigger anomaly detection in near-real-time.

**Q: How is the knowledge base updated?**
A: Add new PDF documents to `docs/`, then re-run `scripts/build_rag_from_pdfs.py` to rebuild the vector store. In production, this would be automated via a pipeline trigger.
