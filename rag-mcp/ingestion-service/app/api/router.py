from fastapi import APIRouter

from app.api.endpoints import ingestion

api_router = APIRouter()
api_router.include_router(ingestion.router, tags=["ingestion"])
