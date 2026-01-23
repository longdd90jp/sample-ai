# rag.py
from __future__ import annotations

import os
import re
from typing import List, Optional, Tuple

from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from rank_bm25 import BM25Okapi

# ---------- Text normalisation utilities ----------
_STOPWORDS = {
    "a","an","the","and","or","but","if","then","else","to","of","in","on","for","with",
    "as","at","by","from","is","are","was","were","be","been","it","this","that","these",
    "those","you","your","we","our","they","their","i","me","my"
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")

def _tokenize(text: str) -> List[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


# ---------- Embeddings factory (avoid import-time provider calls) ----------
def make_embeddings(openai_api_key: Optional[str] = None) -> OpenAIEmbeddings:
    key = openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY must be set for embeddings.")
    return OpenAIEmbeddings(openai_api_key=key)


# ---------- Build / Load / Save FAISS ----------
def build_index(
    pages: List[Tuple[str, str]],
    openai_api_key: Optional[str] = None
) -> FAISS:
    """
    Build a FAISS index from (source, text) pairs.
    ⚠️ This function calls the embeddings provider and can be slow/expensive.
    It should be run OFFLINE (e.g., admin job, CI pipeline), not at app import time.
    """
    emb = make_embeddings(openai_api_key=openai_api_key)
    docs = [Document(page_content=txt, metadata={"source": src}) for src, txt in pages]
    return FAISS.from_documents(docs, emb)


def save_index(index: FAISS, path: str) -> None:
    """
    Persist FAISS index + metadata locally for fast startup.
    """
    index.save_local(path)


def load_index(
    path: str,
    openai_api_key: Optional[str] = None
) -> FAISS:
    """
    Load a persisted FAISS index from disk.
    This is the recommended approach for application startup:
    fast, cheap, and avoids embedding calls.
    """
    emb = make_embeddings(openai_api_key=openai_api_key)
    return FAISS.load_local(
        path,
        emb,
        allow_dangerous_deserialization=True
    )


# ---------- Retrieval ----------
def retrieve(index: FAISS, query: str, k: int = 5) -> List[Document]:
    return index.similarity_search(query, k=k)


# ---------- Better lexical rerank (BM25) ----------
def rerank_bm25(query: str, docs: List[Document], top_n: int = 3) -> List[Document]:
    """
    Cheap but effective lexical reranker using BM25.
    Intended as a second-stage reranker after vector similarity search.
    """
    if not docs:
        return []

    corpus_tokens = [_tokenize(d.page_content) for d in docs]
    bm25 = BM25Okapi(corpus_tokens)

    q_tokens = _tokenize(query)
    scores = bm25.get_scores(q_tokens)

    ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
    return [d for _, d in ranked[:top_n]]


# ---------- Offline / Admin job example ----------
if __name__ == "__main__":
    """
    Example: build and persist the FAISS index once (offline job).
    Run this manually or in CI/CD:
      python rag.py
    """
    PAGES = [
        ("handbook", "All customer data must be encrypted at rest."),
        ("finance", "Refunds above $500 require manager approval."),
    ]

    index = build_index(PAGES)
    save_index(index, "./faiss_index")