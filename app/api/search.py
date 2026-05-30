"""
GET /api/search – Document search over the retail knowledge base (RAG).
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.rag.retriever import retrieve

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchResult(BaseModel):
    content: str
    source: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., min_length=2, example="return policy"),
    k: int = Query(3, ge=1, le=10),
):
    """Search the retail knowledge base using semantic similarity."""
    try:
        docs = retrieve(q, k=k)
        results = [
            SearchResult(
                content=d["content"],
                source=d.get("metadata", {}).get("source", "Knowledge Base"),
                score=round(d["score"], 4),
            )
            for d in docs
        ]
        logger.info("Search '%s' returned %d results", q, len(results))
        return SearchResponse(query=q, results=results, total=len(results))

    except Exception as exc:
        logger.error("Search error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(exc)}")
