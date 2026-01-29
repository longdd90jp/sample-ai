import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from openai import AzureOpenAI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

load_dotenv()

app = FastAPI(title="ingestion-service")

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = (
    os.getenv("AZURE_OPENAI_API_VERSION")
    or os.getenv("OPENAI_API_VERSION", "2024-02-01")
)
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)
qdrant = QdrantClient(url=QDRANT_URL)


class EmbedRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    text = text.strip()
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, 0)
    return [c for c in chunks if c]


def get_embeddings(texts: List[str]) -> List[List[float]]:
    if not AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
        raise HTTPException(status_code=500, detail="Missing AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    response = client.embeddings.create(model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT, input=texts)
    return [item.embedding for item in response.data]


def ensure_collection(vector_size: int) -> None:
    collections = qdrant.get_collections().collections
    if not any(c.name == QDRANT_COLLECTION for c in collections):
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_embeddings(texts: List[str], embeddings: List[List[float]], metadata: Dict[str, Any]) -> List[str]:
    ensure_collection(len(embeddings[0]))
    points = []
    ids = []
    doc_id = metadata.get("doc_id") or str(uuid4())
    for idx, (text, vector) in enumerate(zip(texts, embeddings)):
        point_id = f"{doc_id}-{idx}"
        ids.append(point_id)
        payload = {"text": text, **metadata, "doc_id": doc_id}
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))
    qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return ids


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="Only UTF-8 text files are supported") from exc

    chunks = chunk_text(text)
    embeddings = get_embeddings(chunks)
    metadata = {"filename": file.filename}
    ids = upsert_embeddings(chunks, embeddings, metadata)
    return {"filename": file.filename, "chunks": len(chunks), "ids": ids}


@app.post("/embed")
async def embed(request: EmbedRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")
    chunks = chunk_text(request.text)
    embeddings = get_embeddings(chunks)
    metadata = request.metadata or {}
    ids = upsert_embeddings(chunks, embeddings, metadata)
    return {"chunks": len(chunks), "ids": ids}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
