from __future__ import annotations

import os
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

MCP_URL = os.getenv("MCP_URL", "http://localhost:8000/mcp")

app = FastAPI(title="MCP Test Client", version="1.0.0")


def _build_args(action: str, params: dict[str, Any]) -> dict[str, Any]:
    if action == "process_data":
        if "input" not in params:
            raise HTTPException(status_code=400, detail="Missing 'input'")
        return {"input": params["input"]}
    if action == "add":
        if "a" not in params or "b" not in params:
            raise HTTPException(status_code=400, detail="Missing 'a' or 'b'")
        return {"a": int(params["a"]), "b": int(params["b"])}
    if action == "find_products":
        if "query" not in params:
            raise HTTPException(status_code=400, detail="Missing 'query'")
        args: dict[str, Any] = {"query": params["query"]}
        if "category" in params and params["category"] is not None:
            args["category"] = params["category"]
        return args
    raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")


async def _call_tool(action: str, args: dict[str, Any]) -> Any:
    transport = StreamableHttpTransport(url=MCP_URL)
    client = Client(transport)
    async with client:
        return await client.call_tool(action, args)


async def _list_tools() -> list[dict[str, Any]]:
    transport = StreamableHttpTransport(url=MCP_URL)
    client = Client(transport)
    async with client:
        tools = await client.list_tools()
        # Tools are pydantic models
        return [tool.model_dump() for tool in tools]


@app.get("/mcp/tool")
async def call_tool_get(
    action: str = Query(..., description="Tool name: process_data | add | find_products"),
    input: str | None = Query(None),
    a: int | None = Query(None),
    b: int | None = Query(None),
    query: str | None = Query(None),
    category: str | None = Query(None),
):
    params: dict[str, Any] = {
        "input": input,
        "a": a,
        "b": b,
        "query": query,
        "category": category,
    }
    args = _build_args(action, {k: v for k, v in params.items() if v is not None})
    result = await _call_tool(action, args)
    return {"action": action, "args": args, "result": result}


@app.post("/mcp/tool")
async def call_tool_post(
    action: str = Query(..., description="Tool name: process_data | add | find_products"),
    payload: dict[str, Any] = Body(default_factory=dict),
):
    args = _build_args(action, payload)
    result = await _call_tool(action, args)
    return {"action": action, "args": args, "result": result}


@app.get("/health")
async def health():
    return {"status": "ok", "mcp_url": MCP_URL}


@app.get("/mcp/tools")
async def list_tools():
    tools = await _list_tools()
    return {"count": len(tools), "tools": tools}
