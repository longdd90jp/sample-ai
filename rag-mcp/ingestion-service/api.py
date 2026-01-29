from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from config import settings
from embeddings import EmbeddingClient
from ingestion import ingest_records
from qdrant_client import QdrantStore

app = FastAPI(title="ingestion-service")


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    category: Optional[str] = None


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...)):
    # Accept JSON or JSONL files containing Q&A records.
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    content = await file.read()
    try:
        raw = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="Only UTF-8 text files are supported") from exc

    result = ingest_records(raw, file.filename, settings.qdrant_batch_size)
    return result


@app.post("/api/search")
async def search(request: SearchRequest):
    # Simple similarity search with optional category filter.
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty")

    embedder = EmbeddingClient()
    store = QdrantStore()
    query_vector = embedder.embed_texts([query])[0]
    top_k = request.top_k or settings.search_top_k

    hits = store.search(query_vector, top_k=top_k, category=request.category)
    results = []
    for hit in hits:
        payload = hit.payload or {}
        results.append(
            {
                "id": hit.id,
                "score": hit.score,
                "category": payload.get("category", ""),
                "question": payload.get("question", ""),
                "answer": payload.get("answer", ""),
                "source": payload.get("source", ""),
            }
        )
    return {"query": query, "results": results}
