from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FAQCreate(BaseModel):
    category_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class FAQUpdate(BaseModel):
    category_id: str | None = Field(None, min_length=1)
    question: str | None = Field(None, min_length=1)
    answer: str | None = Field(None, min_length=1)


class FAQResponse(BaseModel):
    id: str
    category_id: str
    question: str
    answer: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)


class SyncResponse(BaseModel):
    indexed: int


class ErrorEnvelope(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorEnvelope

