"""
RAG Vector Store – Azure AI Search (primary) + TF-IDF fallback.

Priority:
  1. Azure AI Search  – full vector search using Azure OpenAI embeddings
  2. FAISS            – local vector search (if faiss-cpu installed + Azure OpenAI key)
  3. TF-IDF           – keyword similarity, no API key required

Azure AI Search index schema
─────────────────────────────
  id          : Edm.String  (key)
  content     : Edm.String  (searchable)
  source      : Edm.String  (filterable)
  file        : Edm.String
  chunk       : Edm.Int32
  embedding   : Collection(Edm.Single)  (1536-dim, vector search)
"""
import logging
import os
import pickle
from typing import List, Tuple, Dict, Any

import numpy as np

logger = logging.getLogger(__name__)

VECTORSTORE_PATH = os.path.join("vectorstore", "tfidf_index.pkl")
FAISS_DIR = "vectorstore/faiss_index"

# Azure AI Search vector field dimensions (text-embedding-ada-002 → 1536)
EMBEDDING_DIM = 1536


# ─────────────────────────────────────────────────────────────────────────────
# TF-IDF fallback (zero dependencies beyond scikit-learn)
# ─────────────────────────────────────────────────────────────────────────────

class TFIDFVectorStore:
    """Lightweight in-memory vector store using TF-IDF cosine similarity."""

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        self.docs: List[str] = []
        self.metadata: List[dict] = []
        self.matrix = None

    def add_documents(self, texts: List[str], metadatas: List[dict] = None):
        self.docs.extend(texts)
        self.metadata.extend(metadatas or [{} for _ in texts])
        self.matrix = self.vectorizer.fit_transform(self.docs)
        logger.info("TF-IDF store: %d documents indexed", len(self.docs))

    def similarity_search(self, query: str, k: int = 3) -> List[Tuple[str, dict, float]]:
        if self.matrix is None or len(self.docs) == 0:
            return []
        from sklearn.metrics.pairwise import cosine_similarity
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix).flatten()
        top_k = np.argsort(sims)[::-1][:k]
        return [(self.docs[i], self.metadata[i], float(sims[i])) for i in top_k]

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str) -> "TFIDFVectorStore":
        with open(path, "rb") as f:
            return pickle.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# Azure AI Search helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_azure_embeddings_client():
    """Return an AzureOpenAIEmbeddings instance or raise."""
    from langchain_openai import AzureOpenAIEmbeddings
    from app.core.config import settings

    if not settings.use_azure_openai:
        raise ValueError("Azure OpenAI credentials not configured")

    return AzureOpenAIEmbeddings(
        azure_deployment=settings.azure_openai_embedding_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def _ensure_azure_search_index():
    """
    Create the Azure AI Search index if it does not already exist.
    The index has a vector field 'embedding' (1536 dims, HNSW algorithm).
    """
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        SearchIndex,
        SearchField,
        SearchFieldDataType,
        SimpleField,
        SearchableField,
        VectorSearch,
        HnswAlgorithmConfiguration,
        VectorSearchProfile,
        SearchField as VectorField,
    )
    from azure.core.credentials import AzureKeyCredential
    from app.core.config import settings

    client = SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )

    index_name = settings.azure_search_index_name

    # Check if index already exists
    existing = [idx.name for idx in client.list_indexes()]
    if index_name in existing:
        logger.info("Azure AI Search index '%s' already exists", index_name)
        return

    # Define fields
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="file", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="chunk", type=SearchFieldDataType.Int32, filterable=True),
        VectorField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIM,
            vector_search_profile_name="retail-hnsw-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="retail-hnsw")],
        profiles=[VectorSearchProfile(name="retail-hnsw-profile", algorithm_configuration_name="retail-hnsw")],
    )

    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
    client.create_index(index)
    logger.info("Azure AI Search index '%s' created", index_name)


def _build_azure_search_store(texts: List[str], metadatas: List[dict]):
    """
    Embed all texts with Azure OpenAI and upload to Azure AI Search.
    Returns an AzureSearch LangChain vector store wrapper.
    """
    from langchain_community.vectorstores.azuresearch import AzureSearch
    from app.core.config import settings

    embeddings = _get_azure_embeddings_client()

    # Ensure the index exists before uploading
    _ensure_azure_search_index()

    from langchain.schema import Document
    docs = [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]

    store = AzureSearch(
        azure_search_endpoint=settings.azure_search_endpoint,
        azure_search_key=settings.azure_search_api_key,
        index_name=settings.azure_search_index_name,
        embedding_function=embeddings.embed_query,
    )
    store.add_documents(docs)
    logger.info(
        "Azure AI Search: indexed %d documents into '%s'",
        len(docs),
        settings.azure_search_index_name,
    )
    return store


def _load_azure_search_store():
    """Load an existing Azure AI Search vector store (no re-indexing)."""
    try:
        from langchain_community.vectorstores.azuresearch import AzureSearch
        from app.core.config import settings

        embeddings = _get_azure_embeddings_client()

        store = AzureSearch(
            azure_search_endpoint=settings.azure_search_endpoint,
            azure_search_key=settings.azure_search_api_key,
            index_name=settings.azure_search_index_name,
            embedding_function=embeddings.embed_query,
        )
        logger.info(
            "Azure AI Search store loaded (index: '%s')",
            settings.azure_search_index_name,
        )
        return store
    except Exception as exc:
        logger.warning("Could not load Azure AI Search store: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# FAISS fallback (local, requires faiss-cpu + Azure OpenAI)
# ─────────────────────────────────────────────────────────────────────────────

def _try_faiss_store(texts: List[str], metadatas: List[dict]):
    """Build a local FAISS store using Azure OpenAI embeddings."""
    try:
        from langchain_community.vectorstores import FAISS
        from langchain.schema import Document
        from app.core.config import settings

        if not settings.use_azure_openai:
            raise ValueError("Azure OpenAI not configured")

        embeddings = _get_azure_embeddings_client()
        docs = [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]
        store = FAISS.from_documents(docs, embeddings)
        logger.info("FAISS store built with Azure OpenAI embeddings (%d docs)", len(docs))
        return store
    except Exception as exc:
        logger.warning("FAISS/Azure embeddings unavailable (%s) – using TF-IDF", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def build_vectorstore(texts: List[str], metadatas: List[dict] = None):
    """
    Build and persist the vector store.

    Tries in order:
      1. Azure AI Search  (if AZURE_SEARCH_ENDPOINT + AZURE_SEARCH_API_KEY set)
      2. FAISS            (if faiss-cpu installed + Azure OpenAI configured)
      3. TF-IDF           (always available)
    """
    metadatas = metadatas or [{} for _ in texts]
    from app.core.config import settings

    # ── 1. Azure AI Search ───────────────────────────────────────
    if settings.use_azure_search:
        try:
            store = _build_azure_search_store(texts, metadatas)
            # Persist a local marker so load_vectorstore knows Azure is the source
            os.makedirs("vectorstore", exist_ok=True)
            with open("vectorstore/backend.txt", "w") as f:
                f.write("azure_search")
            return store
        except Exception as exc:
            logger.warning("Azure AI Search indexing failed (%s) – falling back", exc)

    # ── 2. FAISS ─────────────────────────────────────────────────
    faiss_store = _try_faiss_store(texts, metadatas)
    if faiss_store is not None:
        os.makedirs("vectorstore", exist_ok=True)
        faiss_store.save_local(FAISS_DIR)
        with open("vectorstore/backend.txt", "w") as f:
            f.write("faiss")
        logger.info("FAISS index saved to %s", FAISS_DIR)
        return faiss_store

    # ── 3. TF-IDF ────────────────────────────────────────────────
    store = TFIDFVectorStore()
    store.add_documents(texts, metadatas)
    store.save(VECTORSTORE_PATH)
    os.makedirs("vectorstore", exist_ok=True)
    with open("vectorstore/backend.txt", "w") as f:
        f.write("tfidf")
    return store


def load_vectorstore():
    """
    Load the persisted vector store.

    Reads vectorstore/backend.txt to determine which backend was used,
    then loads accordingly.
    """
    backend_file = "vectorstore/backend.txt"
    backend = None

    if os.path.exists(backend_file):
        with open(backend_file) as f:
            backend = f.read().strip()

    from app.core.config import settings

    # ── Azure AI Search ──────────────────────────────────────────
    if backend == "azure_search" or (settings.use_azure_search and backend is None):
        store = _load_azure_search_store()
        if store is not None:
            return store

    # ── FAISS ────────────────────────────────────────────────────
    if (backend == "faiss" or backend is None) and os.path.exists(FAISS_DIR):
        try:
            from langchain_community.vectorstores import FAISS
            embeddings = _get_azure_embeddings_client()
            store = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
            logger.info("FAISS index loaded from %s", FAISS_DIR)
            return store
        except Exception as exc:
            logger.warning("Could not load FAISS index: %s", exc)

    # ── TF-IDF ───────────────────────────────────────────────────
    if os.path.exists(VECTORSTORE_PATH):
        logger.info("Loading TF-IDF vector store from %s", VECTORSTORE_PATH)
        return TFIDFVectorStore.load(VECTORSTORE_PATH)

    logger.warning(
        "No vector store found – run 'python scripts/build_rag_from_pdfs.py' first"
    )
    return None
