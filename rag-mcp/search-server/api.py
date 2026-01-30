from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from search_service import SearchService

app = FastAPI(title="search-server")
service = SearchService()


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None


@app.post("/search")
async def search(request: SearchRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty")
    return service.search(query, top_k=request.top_k)
