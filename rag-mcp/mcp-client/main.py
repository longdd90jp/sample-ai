import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="mcp-client")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8003")


class QueryRequest(BaseModel):
    query: str
    top_k: int | None = None


@app.post("/api/search")
async def api_search(request: QueryRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty")
    payload = {"query": query, "top_k": request.top_k}
    async with httpx.AsyncClient(timeout=30) as http:
        response = await http.post(f"{MCP_SERVER_URL}/query", json=payload)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
