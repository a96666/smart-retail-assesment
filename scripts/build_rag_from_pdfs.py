"""
build_rag_from_pdfs.py
──────────────────────
Reads all PDFs from docs/, chunks the text, and indexes them into:

  PRIMARY  → Azure AI Search (vector search with Azure OpenAI embeddings)
  FALLBACK → FAISS local index (if faiss-cpu installed + Azure OpenAI key)
  FALLBACK → TF-IDF pickle    (always works, no API key needed)

Usage:
  python scripts/build_rag_from_pdfs.py

Prerequisites (Azure path):
  pip install azure-search-documents langchain-community langchain-openai pypdf

Environment variables required for Azure AI Search:
  AZURE_SEARCH_ENDPOINT   = https://<your-service>.search.windows.net
  AZURE_SEARCH_API_KEY    = <your-admin-key>
  AZURE_OPENAI_API_KEY    = <your-openai-key>
  AZURE_OPENAI_ENDPOINT   = https://<your-resource>.openai.azure.com/
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT = text-embedding-ada-002
"""

import os
import re
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("rag_builder")

DOCS_DIR = "docs"
CHUNK_SIZE = 400       # characters per chunk
CHUNK_OVERLAP = 80     # overlap between chunks


# ─────────────────────────────────────────────────────────────────────────────
# PDF text extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text
    except ImportError:
        logger.error("pypdf not installed. Run: pip install pypdf")
        return ""
    except Exception as exc:
        logger.error("Failed to read %s: %s", pdf_path, exc)
        return ""


def clean_text(text: str) -> str:
    """Clean extracted PDF text."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"Page \d+ \|.*\n", "", text)
    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Text chunking
# ─────────────────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split text into overlapping chunks, preferring sentence boundaries."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Try to break at sentence boundary
        last_period = chunk.rfind(". ")
        if last_period > chunk_size // 2:
            chunk = chunk[: last_period + 1]
        chunk = chunk.strip()
        if len(chunk) > 50:
            chunks.append(chunk)
        start += max(1, len(chunk) - overlap)
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# Main builder
# ─────────────────────────────────────────────────────────────────────────────

def build_rag(docs_dir: str = DOCS_DIR):
    """
    Index all PDFs in docs_dir into the configured vector store backend.
    Returns the built store object.
    """
    if not os.path.exists(docs_dir):
        logger.error(
            "docs/ directory not found. Run 'python scripts/create_pdf_docs.py' first."
        )
        sys.exit(1)

    pdf_files = sorted(f for f in os.listdir(docs_dir) if f.endswith(".pdf"))

    if not pdf_files:
        logger.error(
            "No PDF files found in %s/. Run 'python scripts/create_pdf_docs.py' first.",
            docs_dir,
        )
        sys.exit(1)

    logger.info("Found %d PDF files in %s/", len(pdf_files), docs_dir)

    all_texts = []
    all_metadata = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(docs_dir, pdf_file)
        logger.info("Processing: %s", pdf_file)

        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text.strip():
            logger.warning("  No text extracted from %s – skipping", pdf_file)
            continue

        clean = clean_text(raw_text)
        chunks = chunk_text(clean)

        doc_name = pdf_file.replace(".pdf", "").replace("_", " ")
        for i, chunk in enumerate(chunks):
            all_texts.append(chunk)
            all_metadata.append({
                "source": doc_name,
                "file": pdf_file,
                "chunk": i,
            })

        logger.info("  → %d chunks extracted", len(chunks))

    if not all_texts:
        logger.error("No text could be extracted from any PDF. Aborting.")
        sys.exit(1)

    logger.info("Total chunks to index: %d", len(all_texts))

    # ── Show which backend will be used ──────────────────────────
    from app.core.config import settings
    if settings.use_azure_search:
        logger.info(
            "Backend: Azure AI Search  (endpoint: %s, index: %s)",
            settings.azure_search_endpoint,
            settings.azure_search_index_name,
        )
    elif settings.use_azure_openai:
        logger.info("Backend: FAISS (local) with Azure OpenAI embeddings")
    else:
        logger.info("Backend: TF-IDF (no Azure credentials configured)")

    # ── Build vector store ────────────────────────────────────────
    os.makedirs("vectorstore", exist_ok=True)
    from app.rag.embeddings import build_vectorstore
    store = build_vectorstore(all_texts, all_metadata)

    logger.info(
        "RAG vector store built successfully from %d PDFs (%d chunks)",
        len(pdf_files),
        len(all_texts),
    )
    return store


if __name__ == "__main__":
    build_rag()
