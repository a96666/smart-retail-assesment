"""
RAG retrieval logic – wraps the vector store with a clean interface.

Supports three backends transparently:
  • Azure AI Search  (LangChain AzureSearch wrapper)
  • FAISS            (LangChain FAISS wrapper)
  • TF-IDF           (custom TFIDFVectorStore)
"""
import logging
from typing import List, Dict, Any

from app.rag.embeddings import load_vectorstore, TFIDFVectorStore

logger = logging.getLogger(__name__)

_store = None


def get_store():
    global _store
    if _store is None:
        _store = load_vectorstore()
    return _store


def reset_store():
    """Force reload of the vector store (useful after re-indexing)."""
    global _store
    _store = None


def retrieve(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieve top-k relevant documents for a query.

    Returns a list of dicts:
      { 'content': str, 'metadata': dict, 'score': float }
    """
    store = get_store()
    if store is None:
        logger.warning("Vector store not available – returning empty results")
        return []

    try:
        # ── LangChain stores (Azure AI Search & FAISS) ───────────
        if hasattr(store, "similarity_search_with_relevance_scores"):
            # AzureSearch returns (doc, score) where score is 0-1 relevance
            results = store.similarity_search_with_relevance_scores(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                }
                for doc, score in results
            ]

        if hasattr(store, "similarity_search_with_score"):
            # FAISS returns (doc, L2-distance) – lower is better
            results = store.similarity_search_with_score(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                }
                for doc, score in results
            ]

        # ── TF-IDF fallback ──────────────────────────────────────
        if isinstance(store, TFIDFVectorStore):
            results = store.similarity_search(query, k=k)
            return [
                {"content": text, "metadata": meta, "score": score}
                for text, meta, score in results
            ]

    except Exception as exc:
        logger.error("Retrieval error: %s", exc, exc_info=True)

    return []


def format_context(docs: List[Dict[str, Any]]) -> str:
    """Format retrieved docs into a context string for the LLM prompt."""
    if not docs:
        return "No relevant documents found."
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.get("metadata", {}).get("source", f"Document {i}")
        parts.append(f"[{i}] Source: {source}\n{doc['content']}")
    return "\n\n".join(parts)
