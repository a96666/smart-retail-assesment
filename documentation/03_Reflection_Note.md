# Reflection Note
## Smart Retail Assistant – Capstone Project
### Left Shift Program 2026 – Data & AI (T5)

---

## 1. Project Summary

This capstone project involved designing and building a complete **Multi-Agent AI Platform** for the Smart Retail domain from scratch. The platform integrates demand forecasting, customer Q&A via RAG, and anomaly detection into a unified system backed by a FastAPI backend, machine learning models, a vector store, and Azure cloud services.

The project was completed as an individual effort and covers all mandatory components: Python fullstack, ML/DL, GenAI/Agents, Azure AI & Cloud, Data Engineering Pipeline, Analytics & Visualization, and Final Deployment.

---

## 2. Challenges Encountered

### 2.1 Multi-Agent Orchestration Design
**Challenge:** Deciding how agents should communicate and how to route user queries to the right agent without over-engineering the system.

**What I tried:** Initially considered a full LangChain agent with tool-calling, but this added significant complexity and latency for a demo system.

**Resolution:** Implemented a lightweight keyword-based intent classifier in the orchestrator. This is fast, transparent, and easy to debug. The architecture is designed so it can be upgraded to LLM-based intent classification (e.g., using a function-calling model) without changing the agent interfaces.

**Learning:** Start simple and make it work before adding complexity. A rule-based router is often sufficient and more reliable than an LLM-based one for well-defined intents.

---

### 2.2 RAG Without Azure OpenAI Keys
**Challenge:** The RAG system requires embeddings to build the FAISS vector store, but Azure OpenAI keys are not always available during development.

**Resolution:** Built a dual-mode system — FAISS with Azure OpenAI embeddings when configured, and a TF-IDF cosine similarity fallback when not. This means the system works end-to-end without any API keys, making it easy to demo and test locally.

**Learning:** Always design AI systems with graceful degradation. A mock or fallback path is not just for testing — it's essential for demos, CI/CD pipelines, and cost control.

---

### 2.3 Async SQLAlchemy with FastAPI
**Challenge:** SQLAlchemy's async engine requires careful session management. Early versions had session leaks and "greenlet_spawn" errors when mixing sync and async code.

**Resolution:** Used `async_sessionmaker` with proper `try/except/finally` in the `get_db()` dependency. Ensured all ORM operations use `await` and that sessions are always closed.

**Learning:** Async database access in Python requires understanding the event loop carefully. The FastAPI dependency injection pattern (`Depends(get_db)`) is the cleanest way to manage session lifecycle.

---

### 2.4 Feature Engineering for Time-Series Forecasting
**Challenge:** The Random Forest model needs lag features, but generating them correctly for prediction (not just training) requires careful handling of the rolling window.

**Resolution:** During training, lag features are computed from the full historical dataset. During inference, the last known values are used as the initial lag window, and predictions are fed back as new lag values for multi-step forecasting.

**Learning:** The gap between training and inference is where most ML bugs hide. Always test the inference path separately from the training path.

---

### 2.5 Anomaly Detection Threshold Tuning
**Challenge:** The Isolation Forest `contamination` parameter directly controls how many records are flagged. Too high and everything looks anomalous; too low and real spikes are missed.

**Resolution:** Set contamination to 2% based on the known anomaly injection rate in the synthetic dataset (1.5% spikes + 0.8% stockouts ≈ 2.3%). Added a z-score fallback with a 2.5 standard deviation threshold as a sanity check.

**Learning:** Anomaly detection is inherently unsupervised and threshold-dependent. In production, the threshold should be tuned based on business feedback (how many false positives the operations team can tolerate).

---

### 2.6 PDF Knowledge Base Quality
**Challenge:** PDF text extraction is noisy — headers, footers, and table formatting often produce garbled text that degrades RAG quality.

**Resolution:** Added a `clean_text()` function that removes page numbers, excessive whitespace, and header/footer patterns. Used overlapping chunks (400 chars with 80-char overlap) to avoid cutting sentences mid-way.

**Learning:** RAG quality is 80% about data quality. Garbage in, garbage out. Investing time in the chunking and cleaning strategy pays off more than tuning the retrieval parameters.

---

## 3. Key Learnings

### Technical Learnings

| Area | Learning |
|---|---|
| FastAPI | Lifespan context managers are the right way to handle startup/shutdown. Pydantic v2 is significantly faster than v1 for validation. |
| SQLAlchemy | Async ORM requires `mapped_column` and `Mapped` type hints in SQLAlchemy 2.0. The old `Column()` style still works but is deprecated. |
| scikit-learn | `joblib.dump/load` is more reliable than `pickle` for sklearn models, especially across Python versions. |
| LangChain | LangChain's abstraction is powerful but adds significant overhead. For simple RAG, a direct FAISS + OpenAI call is often cleaner. |
| Docker | Multi-stage builds significantly reduce image size (builder stage with gcc vs. slim runtime). |
| GitHub Actions | Caching pip dependencies with `cache: "pip"` in `setup-python` cuts CI time by ~60%. |

### Architecture Learnings

1. **Separation of concerns** — keeping agents, ML models, and RAG as independent modules made testing and debugging much easier.
2. **Fallback-first design** — every external dependency (Azure OpenAI, model files, vector store) has a fallback, making the system resilient.
3. **Async all the way** — mixing sync and async code in FastAPI causes subtle bugs. Commit to async from the start.
4. **Data pipeline as code** — treating the data pipeline as a first-class Python module (not a notebook) makes it reproducible and testable.

---

## 4. Optimisations Made

### Performance
- **Lazy model loading:** ML models are loaded once on first use and cached in memory, not on every request.
- **Async DB sessions:** All database operations are non-blocking, allowing the server to handle concurrent requests efficiently.
- **Vector store caching:** The FAISS/TF-IDF index is loaded once at startup and reused across all search requests.

### Code Quality
- **Pydantic models** on all API inputs/outputs — catches bad data at the boundary.
- **Structured logging** with consistent format across all modules.
- **Global exception handler** — prevents unhandled errors from crashing the server.
- **Pytest fixtures** with session-scoped DB setup — tests run in isolation without polluting each other.

### ML Quality
- **Outlier capping** in the staging step prevents extreme values from distorting model training.
- **Confidence intervals** on forecasts give users a sense of uncertainty, not just a point estimate.
- **Anomaly descriptions** generated by the LLM make alerts actionable, not just numbers.

---

## 5. What I Would Do Differently

1. **Use a proper embedding model from the start** — TF-IDF is a good fallback but semantic search with real embeddings is noticeably better for Q&A quality.

2. **Add authentication** — the current API has no auth. In production, Azure AD or API key middleware should be added before deployment.

3. **Implement streaming responses** — for the agent chat, streaming the LLM response token-by-token would make the UI feel much more responsive.

4. **Use Azure Fabric / Databricks for the pipeline** — the current pipeline runs locally. In production, Azure Data Factory + Databricks would handle scale and scheduling.

5. **Add a proper evaluation framework** — for the RAG system, I would add RAGAS or a similar framework to measure retrieval precision and answer faithfulness.

6. **More agent types** — a Pricing Optimisation Agent and an Inventory Replenishment Agent would add significant business value.

---

## 6. Future Enhancements

| Enhancement | Priority | Effort |
|---|---|---|
| Azure AD authentication | High | Medium |
| Streaming LLM responses | High | Low |
| Real-time anomaly detection (Event Hub) | High | High |
| LLM-based intent classification | Medium | Low |
| RAGAS evaluation for RAG quality | Medium | Medium |
| Pricing optimisation agent | Medium | High |
| Power BI embedded in frontend | Low | Medium |
| LLM fine-tuning on retail data | Low | Very High |
| Multi-tenant support | Low | High |

---

## 7. Conclusion

This project successfully demonstrates an end-to-end Multi-Agent AI Platform that integrates all the required components of the Left Shift Program T5 capstone. The system is functional, well-structured, and designed with production readiness in mind — including fallback mechanisms, structured logging, input validation, and CI/CD.

The biggest takeaway from this project is that **the integration between components is harder than building each component individually**. Making the ML model, the RAG system, the agents, and the API work together reliably required careful design of interfaces and extensive testing.

The project has given me hands-on experience with the full Data + AI engineering stack and a solid foundation for building production-grade AI systems.
