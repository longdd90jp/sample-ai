from fastapi import APIRouter, HTTPException

from app.schemas.search import SearchRequest
from app.services.search import SearchService

router = APIRouter()
service = SearchService()


@router.post("/search")
async def search(request: SearchRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty")
    return service.search(query, top_k=request.top_k)
