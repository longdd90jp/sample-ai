# app.py
import os, asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag import build_index
from agent import agent_run

app = FastAPI(title="Agentic AI API")

# Build a tiny demo index (swap with your corpus)
PAGES = [("handbook", "All employees must follow the Q2 compliance checklist."),
         ("policy", "Customer PII must never be returned in chat responses.")]
INDEX = build_index(PAGES)

class AskRequest(BaseModel):
    query: str

@app.post("/ask")
async def ask(req: AskRequest):
    try:
        result = await asyncio.wait_for(agent_run(req.query, INDEX), timeout=25)
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))