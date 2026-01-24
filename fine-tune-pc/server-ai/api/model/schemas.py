from __future__ import annotations

from pydantic import BaseModel, Field


class Storage(BaseModel):
    ssd: str = Field(..., min_length=1)
    hdd: str | None = None


class Spec(BaseModel):
    cpu: str = Field(..., min_length=1)
    mainboard: str = Field(..., min_length=1)
    ram: str = Field(..., min_length=1)
    storage: Storage
    power_supply: str = Field(..., min_length=1)
    case: str = Field(..., min_length=1)


class ContentRequest(BaseModel):
    specs: list[Spec]
    target: str = Field(..., min_length=1)


class GenerateRequest(BaseModel):
    content: ContentRequest
    max_new_tokens: int = 300
    temperature: float = 0.7
    top_p: float = 0.9


class GenerateResponse(BaseModel):
    text: str
