@echo off
echo ============================================================
echo   Smart Retail Assistant - Setup and Run
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo [1/5] Installing dependencies...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo       Done.

echo.
echo [2/5] Generating dataset...
python scripts/generate_dataset.py
if errorlevel 1 (
    echo [WARNING] Dataset generation had issues - continuing...
)

echo.
echo [3/5] Creating PDF knowledge base documents...
python scripts/create_pdf_docs.py
if errorlevel 1 (
    echo [WARNING] PDF creation had issues - text fallback will be used
)

echo.
echo [4/5] Running full pipeline (transform + train models + build RAG)...
python pipeline/run_pipeline.py
if errorlevel 1 (
    echo [ERROR] Pipeline failed.
    pause
    exit /b 1
)

echo.
echo [5/5] Starting API server...
echo.
echo ============================================================
echo   Server starting at: http://localhost:8000
echo   API docs at:        http://localhost:8000/docs
echo   Press Ctrl+C to stop
echo ============================================================
echo.
python -m uvicorn app.main:app --reload --port 8000
