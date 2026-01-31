from fastapi import APIRouter

from app.api.endpoints import search

api_router = APIRouter()
api_router.include_router(search.router, tags=["search"])
