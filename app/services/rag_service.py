import os
from pathlib import Path
from dotenv import load_dotenv

import requests as http_requests
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

DOCS_DIR = Path("docs")
EMBED_MODEL = "gemini-embedding-001"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VECTOR_STORE_BACKEND = os.getenv("VECTOR_STORE", "faiss").lower()

# Pinecone settings (only used when VECTOR_STORE=pinecone)
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag-index")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "docs")

# FAISS settings (only used when VECTOR_STORE=faiss)
FAISS_INDEX_PATH = Path("faiss_index")

_EMBED_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL}:embedContent"
    f"?key={GEMINI_API_KEY}"
)


class _GeminiEmbeddings(Embeddings):
    """LangChain-compatible wrapper calling the Gemini REST API directly (v1)."""

    def _embed_one(self, text: str, task_type: str) -> list[float]:
        payload = {
            "model": f"models/{EMBED_MODEL}",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
        }
        resp = http_requests.post(_EMBED_URL, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["embedding"]["values"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t, "RETRIEVAL_DOCUMENT") for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text, "RETRIEVAL_QUERY")


_embeddings = _GeminiEmbeddings()

_vectorstore = None  # loaded lazily


# ---------------------------------------------------------------------------
# FAISS backend
# ---------------------------------------------------------------------------

def _faiss_load_or_build():
    from langchain_community.vectorstores import FAISS

    index_file = FAISS_INDEX_PATH / "index.faiss"
    if index_file.exists():
        return FAISS.load_local(
            str(FAISS_INDEX_PATH), _embeddings, allow_dangerous_deserialization=True
        )
    return _faiss_build()


def _faiss_build():
    from langchain_community.vectorstores import FAISS

    chunks = _load_chunks()
    vs = FAISS.from_documents(chunks, _embeddings)
    vs.save_local(str(FAISS_INDEX_PATH))
    return vs


# ---------------------------------------------------------------------------
# Pinecone backend
# ---------------------------------------------------------------------------

def _pinecone_client():
    from pinecone import Pinecone
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def _pinecone_ensure_index(pc):
    from pinecone import ServerlessSpec

    existing = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=3072,     # output dim of gemini-embedding-001
            metric="cosine",
            spec=ServerlessSpec(
                cloud=os.getenv("PINECONE_CLOUD", "aws"),
                region=os.getenv("PINECONE_REGION", "us-east-1"),
            ),
        )


def _pinecone_load_or_build():
    from langchain_pinecone import Pinecone as PineconeVectorStore

    pc = _pinecone_client()
    _pinecone_ensure_index(pc)

    index = pc.Index(PINECONE_INDEX_NAME)
    stats = index.describe_index_stats()
    namespace_stats = stats.get("namespaces", {}).get(PINECONE_NAMESPACE, {})
    is_empty = namespace_stats.get("vector_count", 0) == 0

    if is_empty:
        return _pinecone_build()

    return PineconeVectorStore(
        index=index,
        embedding=_embeddings,
        namespace=PINECONE_NAMESPACE,
    )


def _pinecone_build():
    from langchain_pinecone import Pinecone as PineconeVectorStore

    pc = _pinecone_client()
    _pinecone_ensure_index(pc)
    chunks = _load_chunks()

    return PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=_embeddings,
        index_name=PINECONE_INDEX_NAME,
        namespace=PINECONE_NAMESPACE,
    )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_chunks():
    """Load and split documents from docs/ into chunks."""
    if not DOCS_DIR.exists() or not any(DOCS_DIR.iterdir()):
        raise RuntimeError(
            f"No documents found in '{DOCS_DIR}/'. "
            "Add .txt files there before building the index."
        )

    loader = DirectoryLoader(
        str(DOCS_DIR),
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        glob="**/*.txt",
    )
    raw_docs = loader.load()

    if not raw_docs:
        raise RuntimeError("No .txt files loaded from docs/. Check the directory contents.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_documents(raw_docs)


def _load_or_build_index():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    if VECTOR_STORE_BACKEND == "pinecone":
        _vectorstore = _pinecone_load_or_build()
    elif VECTOR_STORE_BACKEND == "faiss":
        _vectorstore = _faiss_load_or_build()
    else:
        raise RuntimeError(
            f"Unknown VECTOR_STORE='{VECTOR_STORE_BACKEND}'. Choose 'faiss' or 'pinecone'."
        )

    return _vectorstore


# ---------------------------------------------------------------------------
# Public API (used by gemini_service.py)
# ---------------------------------------------------------------------------

def retrieve(query: str, k: int = 4) -> list[str]:
    """Return top-k relevant text chunks for a query."""
    vs = _load_or_build_index()
    results = vs.similarity_search(query, k=k)
    return [doc.page_content for doc in results]


def rebuild_index():
    """Force-rebuild the index (call after adding new documents)."""
    global _vectorstore
    if VECTOR_STORE_BACKEND == "pinecone":
        _vectorstore = _pinecone_build()
    else:
        _vectorstore = _faiss_build()
