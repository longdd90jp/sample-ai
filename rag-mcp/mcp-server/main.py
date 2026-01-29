import os
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
from openai import AzureOpenAI
from pydantic import BaseModel

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = (
    os.getenv("AZURE_OPENAI_API_VERSION")
    or os.getenv("OPENAI_API_VERSION", "2024-02-01")
)
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "")

SEARCH_SERVER_URL = os.getenv("SEARCH_SERVER_URL", "http://localhost:8001")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

mcp = FastMCP("mcp-server")
app = FastAPI(title="mcp-server")


class QueryRequest(BaseModel):
    query: str
    top_k: int | None = None


async def call_search_server(query: str, top_k: int | None) -> List[Dict[str, Any]]:
    payload = {"query": query}
    if top_k:
        payload["top_k"] = top_k
    async with httpx.AsyncClient(timeout=30) as http:
        response = await http.post(f"{SEARCH_SERVER_URL}/search", json=payload)
        response.raise_for_status()
        data = response.json()
    return data.get("results", [])


def build_messages(query: str, contexts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    if contexts:
        context_block = "\n\n".join(
            f"[{idx+1}] {item.get('text', '')}".strip()
            for idx, item in enumerate(contexts)
            if item.get("text")
        )
        system = (
            "You are a helpful assistant. Use the provided context to answer the user.\n"
            "If the context is insufficient, say you do not know."
        )
        user = f"Question: {query}\n\nContext:\n{context_block}"
    else:
        system = "You are a helpful assistant."
        user = f"Question: {query}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def generate_answer(messages: List[Dict[str, str]]) -> str:
    if not AZURE_OPENAI_CHAT_DEPLOYMENT:
        raise HTTPException(status_code=500, detail="Missing AZURE_OPENAI_CHAT_DEPLOYMENT")
    response = client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


@mcp.tool()
async def search_knowledge_base(query: str, top_k: int | None = None) -> Dict[str, Any]:
    results = await call_search_server(query, top_k)
    return {"query": query, "results": results}


@app.post("/query")
async def query(request: QueryRequest):
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query is empty")

    contexts = await call_search_server(query_text, request.top_k)
    messages = build_messages(query_text, contexts)
    answer = generate_answer(messages)

    return {"query": query_text, "answer": answer, "sources": contexts}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
