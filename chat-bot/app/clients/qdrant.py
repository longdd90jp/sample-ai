from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import Settings
from app.core import ExternalServiceError


class QdrantClientWrapper:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    @property
    def client(self) -> QdrantClient:
        return self._client

    def create_collection_if_not_exists(self) -> None:
        try:
            existing = {c.name for c in self._client.get_collections().collections}
            if self._settings.QDRANT_COLLECTION in existing:
                return
            self._client.create_collection(
                collection_name=self._settings.QDRANT_COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=self._settings.QDRANT_VECTOR_SIZE,
                    distance=qmodels.Distance.COSINE,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            raise ExternalServiceError(f"Qdrant create_collection failed: {exc}") from exc

