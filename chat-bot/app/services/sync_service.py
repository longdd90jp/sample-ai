from __future__ import annotations

from app.clients.azure_openai import AzureOpenAIClient
from app.clients.qdrant import QdrantClientWrapper
from app.config import Settings
from app.repositories.faq_repository import FAQRepository
from app.repositories.vector_repository import VectorRepository


class SyncService:
    def __init__(
        self,
        settings: Settings,
        faq_repo: FAQRepository,
        openai_client: AzureOpenAIClient,
        qdrant: QdrantClientWrapper,
        vector_repo: VectorRepository,
    ) -> None:
        self._settings = settings
        self._faq_repo = faq_repo
        self._openai = openai_client
        self._qdrant = qdrant
        self._vectors = vector_repo

    def run_full_sync(self) -> int:
        self._qdrant.create_collection_if_not_exists()
        faqs = self._faq_repo.get_all()
        indexed = 0
        for doc in faqs:
            faq_id = str(doc["_id"])
            text = f"Q: {doc.get('question','')}\nA: {doc.get('answer','')}"
            vector = self._openai.embed_text(text)
            payload = {
                "question": doc.get("question", ""),
                "answer": doc.get("answer", ""),
                "category_id": doc.get("category_id", ""),
            }
            self._vectors.upsert_faq_vector(faq_id, vector, payload)
            indexed += 1
        return indexed

