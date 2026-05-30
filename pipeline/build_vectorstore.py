"""
Pipeline Step 5 – Build RAG Vector Store
─────────────────────────────────────────
Reads PDF knowledge base documents from docs/, chunks the text, and
indexes them into the configured vector store backend:

  PRIMARY  → Azure AI Search  (AZURE_SEARCH_ENDPOINT + AZURE_SEARCH_API_KEY)
  FALLBACK → FAISS local       (faiss-cpu + Azure OpenAI key)
  FALLBACK → TF-IDF pickle     (always available)
"""
import os
import logging
from typing import List

logger = logging.getLogger(__name__)


def build(docs_dir: str = "docs"):
    """Build and save the vector store from PDF documents in docs_dir."""
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs("vectorstore", exist_ok=True)

    # Delegate to the dedicated script which handles PDF extraction + chunking
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from scripts.build_rag_from_pdfs import build_rag
    store = build_rag(docs_dir=docs_dir)
    return store


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build()
