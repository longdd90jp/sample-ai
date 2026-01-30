from typing import List, Optional

from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from config import settings
from embeddings import EmbeddingClient
from ingestion import ingest_records, ingest_raw
from mongo_client import MongoStore
from vector_store import QdrantStore
from bson import ObjectId

app = FastAPI(title="ingestion-service")
router = APIRouter(prefix="/api")


class FAQRecord(BaseModel):
    doc_id: str
    question: str
    answer: str
    metadata: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Accept JSON files containing Q&A records.
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    content = await file.read()
    try:
        raw = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="Only UTF-8 text files are supported") from exc

    return ingest_raw(raw, file.filename, settings.qdrant_batch_size)


@router.post("/upsert")
async def upsert(records: List[FAQRecord]):
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    payloads = [record.dict() for record in records]
    return ingest_records(payloads, settings.qdrant_batch_size)


@router.post("/search")
async def search(request: SearchRequest):
    # Two-stage retrieval: question_vector then answer_vector.
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty")

    embedder = EmbeddingClient()
    qdrant = QdrantStore()
    mongo = MongoStore()
    query_vector = embedder.embed_texts([query])[0]

    question_hits = qdrant.search(
        query_vector,
        top_k=1,
        vector_name=settings.question_vector_name,
    )
    if question_hits:
        top_hit = question_hits[0]
        if top_hit.score >= settings.search_threshold:
            payload = top_hit.payload or {}
            doc_id = payload.get("doc_id")
            document = mongo.get_by_id(doc_id) if doc_id else None
            return {
                "mode": "direct_answer",
                "doc_id": doc_id,
                "question": (document or {}).get("question", ""),
                "answer": (document or {}).get("answer", ""),
                "metadata": (document or {}).get("metadata", {}),
            }

    answer_hits = qdrant.search(
        query_vector,
        top_k=3,
        vector_name=settings.answer_vector_name,
    )
    doc_ids = [((hit.payload or {}).get("doc_id")) for hit in answer_hits]
    docs = mongo.get_by_ids([doc_id for doc_id in doc_ids if doc_id])
    docs_by_id = {doc["doc_id"]: doc for doc in docs if "doc_id" in doc}

    suggestions = []
    for doc_id in doc_ids:
        document = docs_by_id.get(doc_id, {})
        if not document:
            continue
        suggestions.append({"doc_id": doc_id, "question": document.get("question", "")})
    return {"mode": "suggest_questions", "suggestions": suggestions}


app.include_router(router)
