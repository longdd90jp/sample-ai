from __future__ import annotations

from typing import Any

from bson.errors import InvalidId

from app.core import EntityNotFoundError, ValidationError
from app.models.schemas import FAQCreate, FAQResponse, FAQUpdate
from app.repositories.faq_repository import FAQRepository
from app.repositories.vector_repository import VectorRepository


class FAQService:
    def __init__(self, repo: FAQRepository, vector_repo: VectorRepository | None = None) -> None:
        self._repo = repo
        self._vector_repo = vector_repo

    def create_faq(self, data: FAQCreate) -> str:
        faq = data.model_dump()
        return self._repo.create(faq)

    def list_faqs(self) -> list[FAQResponse]:
        docs = self._repo.get_all()
        return [self._to_response(d) for d in docs]

    def update_faq(self, faq_id: str, data: FAQUpdate) -> None:
        try:
            updates = {k: v for k, v in data.model_dump().items() if v is not None}
            if not updates:
                raise ValidationError("No fields to update")
            if not self._repo.update(faq_id, updates):
                raise EntityNotFoundError(f"FAQ with id {faq_id} not found")
        except InvalidId as exc:
            raise ValidationError("Invalid FAQ id") from exc

    def delete_faq(self, faq_id: str) -> None:
        try:
            if not self._repo.delete(faq_id):
                raise EntityNotFoundError(f"FAQ with id {faq_id} not found")
            if self._vector_repo is not None:
                self._vector_repo.delete(faq_id)
        except InvalidId as exc:
            raise ValidationError("Invalid FAQ id") from exc

    def get_faq(self, faq_id: str) -> FAQResponse:
        try:
            doc = self._repo.get_by_id(faq_id)
            if not doc:
                raise EntityNotFoundError(f"FAQ with id {faq_id} not found")
            return self._to_response(doc)
        except InvalidId as exc:
            raise ValidationError("Invalid FAQ id") from exc

    @staticmethod
    def _to_response(doc: dict[str, Any]) -> FAQResponse:
        return FAQResponse(
            id=str(doc.get("_id")),
            category_id=str(doc.get("category_id", "")),
            question=str(doc.get("question", "")),
            answer=str(doc.get("answer", "")),
        )

