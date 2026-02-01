from typing import Optional

from pydantic import BaseModel


class FAQRecord(BaseModel):
    doc_id: str
    question: str
    answer: str
    metadata: Optional[dict] = None


class FAQDeleteRequest(BaseModel):
    doc_ids: list[str]
