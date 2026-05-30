"""
Full Pipeline Orchestrator
Runs all pipeline steps in sequence:
  1. Generate dataset (CSV files)
  2. Transform (stage + curate parquet)
  3. Train demand forecasting model
  4. Train anomaly detection model
  5. Create PDF knowledge base documents
  6. Build RAG vector store from PDFs
  7. Seed database with sample data
"""
import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("pipeline")


def run_pipeline():
    logger.info("=" * 65)
    logger.info("  SMART RETAIL ASSISTANT – FULL DATA PIPELINE")
    logger.info("=" * 65)

    # ── Step 1: Generate dataset ─────────────────────────────────
    logger.info("\n[Step 1/7] Generating synthetic retail dataset...")
    from pipeline.ingest import run as ingest_run
    df_raw = ingest_run()
    logger.info("✓ Raw data: %d records", len(df_raw))

    # ── Step 2: Transform ────────────────────────────────────────
    logger.info("\n[Step 2/7] Transforming data (stage → curate)...")
    from pipeline.transform import run as transform_run
    df_curated = transform_run()
    logger.info("✓ Curated: %d records, %d features", len(df_curated), len(df_curated.columns))

    # ── Step 3a: Train demand model ──────────────────────────────
    logger.info("\n[Step 3a/7] Training demand forecasting model (Random Forest)...")
    from pipeline.train_forecast import train as train_forecast
    metrics = train_forecast()
    logger.info("✓ Demand model – MAE: %.2f | RMSE: %.2f", metrics["mae"], metrics["rmse"])

    # ── Step 3b: Train anomaly model ─────────────────────────────
    logger.info("\n[Step 3b/7] Training anomaly detection model (Isolation Forest)...")
    from pipeline.train_anomaly import train as train_anomaly
    a_metrics = train_anomaly()
    logger.info("✓ Anomaly model – Anomaly rate: %.1f%%", a_metrics["anomaly_rate"])

    # ── Step 4: Create PDF docs ──────────────────────────────────
    logger.info("\n[Step 4/7] Creating PDF knowledge base documents...")
    _create_pdfs()

    # ── Step 5: Build RAG vector store ───────────────────────────
    logger.info("\n[Step 5/7] Building RAG vector store from PDFs...")
    _build_rag()

    # ── Step 6: Seed database ────────────────────────────────────
    logger.info("\n[Step 6/7] Seeding database with sample data...")
    _seed_database(df_raw)

    logger.info("\n" + "=" * 65)
    logger.info("  PIPELINE COMPLETE")
    logger.info("  Start the server:  uvicorn app.main:app --reload --port 8000")
    logger.info("  Open browser:      http://localhost:8000")
    logger.info("  API docs:          http://localhost:8000/docs")
    logger.info("=" * 65)


# ── Helpers ──────────────────────────────────────────────────────

def _create_pdfs():
    """Create PDF knowledge base documents."""
    try:
        # Import and run the PDF creator
        import importlib.util, sys as _sys
        spec = importlib.util.spec_from_file_location(
            "create_pdf_docs",
            os.path.join(os.path.dirname(__file__), "..", "scripts", "create_pdf_docs.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        mod.doc_return_policy()
        mod.doc_delivery()
        mod.doc_loyalty()
        mod.doc_warranty()
        mod.doc_store_ops()
        mod.doc_promotions()
        mod.doc_payment()
        mod.doc_support()
        logger.info("✓ 8 PDF documents created in docs/")
    except Exception as exc:
        logger.warning("PDF creation failed (%s) – using text fallback for RAG", exc)
        _create_text_fallback_docs()


def _create_text_fallback_docs():
    """Create plain-text knowledge base if fpdf2 is not installed."""
    os.makedirs("docs", exist_ok=True)
    docs = {
        "Return_Policy.txt": (
            "Return & Refund Policy\n"
            "Most items can be returned within 30 days of purchase in original condition with receipt.\n"
            "Electronics must be returned within 15 days. Sale items are final sale.\n"
            "Refunds are processed within 5-7 business days to the original payment method.\n"
            "Damaged or defective items: contact us within 48 hours of delivery.\n"
        ),
        "Delivery_Guide.txt": (
            "Delivery & Shipping Guide\n"
            "Standard delivery: 3-5 business days, free over $50 otherwise $4.99.\n"
            "Express delivery: 1-2 business days, $9.99.\n"
            "Same-day delivery available in NY, LA, Chicago, Houston, Phoenix for orders before 12 PM.\n"
            "Store pickup (BOPIS): ready in 2 hours, free.\n"
            "International shipping to 50+ countries, 7-14 business days.\n"
        ),
        "Loyalty_Programme.txt": (
            "Smart Rewards Loyalty Programme\n"
            "Earn 1 point per $1 spent. 100 points = $1 discount.\n"
            "Tiers: Bronze (0-$99/mo), Silver ($100-$299), Gold ($300-$699), Platinum ($700+).\n"
            "Gold members get 2x points and free express shipping.\n"
            "Platinum members get 3x points, free express shipping, and VIP events.\n"
            "Points expire after 12 months of inactivity.\n"
        ),
        "Warranty_Support.txt": (
            "Product Warranty & Support\n"
            "Electronics and Appliances: 1-year manufacturer warranty.\n"
            "Footwear and Sports: 6-month warranty.\n"
            "Extended warranty plans available: Smart Protect Basic (+1yr), Plus (+2yr), Premium (+2yr with accidental).\n"
            "To claim: email support@smartretail.com with order number and serial number.\n"
        ),
        "Store_Hours.txt": (
            "Store Operations & Hours\n"
            "Monday-Thursday: 9 AM - 9 PM. Friday-Saturday: 9 AM - 10 PM. Sunday: 10 AM - 6 PM.\n"
            "Stores: Downtown NY, Westfield LA, Northgate Chicago, Eastside Houston, Southpark Phoenix.\n"
            "Services: Personal shopping, click & collect, gift wrapping, product demos, recycling drop-off.\n"
        ),
        "Promotions_Policy.txt": (
            "Promotions & Pricing Policy\n"
            "Summer Sale: Jun 1-15, 20% off Electronics and Accessories.\n"
            "Back to School: Jul 20 - Aug 5, 15% off Sports and Footwear.\n"
            "Flash Weekend: Aug 10-11, 30% off all categories.\n"
            "Only one promo code per order. Price match within 7 days of purchase.\n"
            "Bundle deals: Buy 2 Sports items get 15% off. Buy 2 Electronics get 10% off.\n"
        ),
        "Payment_Methods.txt": (
            "Payment Methods & Security\n"
            "Accepted: Visa, Mastercard, Amex, Discover, PayPal, Apple Pay, Google Pay, Gift Cards, Klarna.\n"
            "Klarna Buy Now Pay Later available for orders over $100 online.\n"
            "Gift cards available in $10, $25, $50, $100, $200 denominations. Never expire.\n"
            "All transactions use 256-bit SSL encryption. PCI DSS Level 1 compliant.\n"
        ),
        "Customer_Support.txt": (
            "Customer Support & Contact Guide\n"
            "Phone: 1-800-RETAIL-1, available 8 AM - 10 PM daily.\n"
            "Email: support@smartretail.com, response within 2 hours.\n"
            "Live chat: smartretail.com, available 8 AM - 10 PM daily.\n"
            "Help centre: help.smartretail.com, 24/7 self-service.\n"
            "Escalation: request Senior Specialist if unresolved within 48 hours.\n"
        ),
    }
    for filename, content in docs.items():
        with open(os.path.join("docs", filename), "w", encoding="utf-8") as f:
            f.write(content)
    logger.info("✓ Text fallback docs created in docs/")


def _build_rag():
    """Build RAG vector store from docs/ folder."""
    import os as _os
    docs_dir = "docs"
    all_texts = []
    all_metadata = []

    # Try PDFs first
    pdf_files = [f for f in _os.listdir(docs_dir) if f.endswith(".pdf")] if _os.path.exists(docs_dir) else []
    txt_files = [f for f in _os.listdir(docs_dir) if f.endswith(".txt")] if _os.path.exists(docs_dir) else []

    if pdf_files:
        try:
            from pypdf import PdfReader
            for pdf_file in sorted(pdf_files):
                path = _os.path.join(docs_dir, pdf_file)
                reader = PdfReader(path)
                text = "\n".join(p.extract_text() or "" for p in reader.pages)
                # Simple chunking
                chunks = [text[i:i+400] for i in range(0, len(text), 320) if len(text[i:i+400]) > 50]
                doc_name = pdf_file.replace(".pdf", "").replace("_", " ")
                for chunk in chunks:
                    all_texts.append(chunk.strip())
                    all_metadata.append({"source": doc_name, "file": pdf_file})
            logger.info("✓ Extracted text from %d PDFs (%d chunks)", len(pdf_files), len(all_texts))
        except ImportError:
            logger.warning("pypdf not installed – falling back to text files")
            pdf_files = []

    if not pdf_files and txt_files:
        for txt_file in sorted(txt_files):
            path = _os.path.join(docs_dir, txt_file)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            chunks = [text[i:i+400] for i in range(0, len(text), 320) if len(text[i:i+400]) > 50]
            doc_name = txt_file.replace(".txt", "").replace("_", " ")
            for chunk in chunks:
                all_texts.append(chunk.strip())
                all_metadata.append({"source": doc_name, "file": txt_file})
        logger.info("✓ Loaded %d text chunks from %d text files", len(all_texts), len(txt_files))

    if not all_texts:
        logger.warning("No documents found – RAG will use keyword fallback")
        return

    from app.rag.embeddings import build_vectorstore
    build_vectorstore(all_texts, all_metadata)
    logger.info("✓ Vector store built with %d chunks", len(all_texts))


def _seed_database(df_raw):
    """Seed the SQLite database with a sample of the raw data."""
    import asyncio
    import pandas as pd

    async def _seed():
        from app.db.database import init_db, AsyncSessionLocal
        from app.db.models import SalesRecord

        await init_db()
        sample = df_raw.sample(min(500, len(df_raw)), random_state=42)

        async with AsyncSessionLocal() as session:
            records = []
            for _, row in sample.iterrows():
                record = SalesRecord(
                    product_id=row["product_id"],
                    product_name=row["product_name"],
                    category=row["category"],
                    quantity=int(row["quantity"]),
                    unit_price=float(row["unit_price"]),
                    total_revenue=float(row["total_revenue"]),
                    sale_date=pd.to_datetime(row["sale_date"]),
                    store_id=row["store_id"],
                )
                records.append(record)
            session.add_all(records)
            await session.commit()
        logger.info("✓ Seeded %d records into database", len(records))

    asyncio.run(_seed())


if __name__ == "__main__":
    run_pipeline()
