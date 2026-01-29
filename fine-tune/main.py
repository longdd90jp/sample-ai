from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import AzureOpenAI

SYSTEM_PROMPT = "Clippy is a factual chatbot that is also sarcastic."


def _load_env() -> None:
    here = Path(__file__).resolve().parent
    parent_env = here.parent / ".env"
    if parent_env.exists():
        load_dotenv(parent_env)
    load_dotenv()


@lru_cache(maxsize=1)
def _get_client() -> AzureOpenAI:
    _load_env()

    api_key = os.getenv("AZURE_OPENAI_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("API_VERSION", "2024-12-01-preview")

    if not api_key or not endpoint:
        raise RuntimeError("Missing AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT")

    return AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=api_key,
    )


class ChatRequest(BaseModel):
    content: str


_load_env()
app = FastAPI()


def _run_chat(model: str, content: str) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        model=model,
    )
    return response.choices[0].message.content


@app.post("/api/test/base")
def test_base(payload: ChatRequest) -> dict:
    model = os.getenv("AZURE_OPENAI_BASE_MODEL")
    if not model:
        raise HTTPException(status_code=500, detail="Missing AZURE_OPENAI_BASE_MODEL")

    return {"content": _run_chat(model, payload.content)}


@app.post("/api/test/fine-tune")
def test_fine_tune(payload: ChatRequest) -> dict:
    model = os.getenv("AZURE_OPENAI_FINE_TUNE_MODEL")
    if not model:
        raise HTTPException(status_code=500, detail="Missing AZURE_OPENAI_FINE_TUNE_MODEL")

    return {"content": _run_chat(model, payload.content)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
