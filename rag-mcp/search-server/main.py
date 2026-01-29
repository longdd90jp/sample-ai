import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import AzureOpenAI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

load_dotenv()

app = FastAPI(title="search-server")

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = (
    os.getenv("AZURE_OPENAI_API_VERSION")
    or os.getenv("OPENAI_API_VERSION", "2024-02-01")
)
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")
DEFAULT_TOP_K = int(os.getenv("SEARCH_TOP_K", "5"))

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)
qdrant = QdrantClient(url=QDRANT_URL)


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None


def get_query_embedding(query: str) -> List[float]:
    if not AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
        raise HTTPException(status_code=500, detail="Missing AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    response = client.embeddings.create(model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT, input=[query])
    return response.data[0].embedding


def ensure_collection(vector_size: int) -> None:
    collections = qdrant.get_collections().collections
    if not any(c.name == QDRANT_COLLECTION for c in collections):
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


@app.post("/search")
async def search(request: SearchRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty")

    embedding = get_query_embedding(query)
    ensure_collection(len(embedding))

    top_k = request.top_k or DEFAULT_TOP_K
    results = qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=embedding,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )

    formatted = []
    for item in results:
        payload = item.payload or {}
        formatted.append(
            {
                "id": item.id,
                "score": item.score,
                "text": payload.get("text", ""),
                "metadata": {k: v for k, v in payload.items() if k != "text"},
            }
        )

    return {"query": query, "results": formatted}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
