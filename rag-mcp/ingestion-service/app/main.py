import asyncio

from fastapi import FastAPI

from app.api.router import api_router
from app.services.embeddings import get_embedding_client

app = FastAPI(title="ingestion-service")
app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def warmup_embeddings() -> None:
    # Load the embedding model once on startup without blocking the event loop.
    await asyncio.to_thread(get_embedding_client)
