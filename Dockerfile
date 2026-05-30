# ── Stage 1: Builder ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app/       ./app/
COPY pipeline/  ./pipeline/
COPY scripts/   ./scripts/
COPY frontend/  ./frontend/

# Create directories for generated artifacts
RUN mkdir -p data/raw data/staged data/curated \
             ml_models vectorstore docs

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_ENV=production

EXPOSE 8000

# Entrypoint: run pipeline (trains models, builds RAG) then start server
CMD ["sh", "-c", \
     "python pipeline/run_pipeline.py && \
      uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
