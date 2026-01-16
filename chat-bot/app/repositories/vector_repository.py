from __future__ import annotations

from typing import Any

from qdrant_client.http import models as qmodels

from app.clients.qdrant import QdrantClientWrapper
from app.config import Settings
from app.core import ExternalServiceError


class VectorRepository:
    def __init__(self, settings: Settings, qdrant: QdrantClientWrapper) -> None:
        self._settings = settings
        self._qdrant = qdrant

    def upsert_faq_vector(self, faq_id: str, vector: list[float], metadata: dict[str, Any]) -> None:
        try:
            point = qmodels.PointStruct(id=faq_id, vector=vector, payload=dict(metadata))
            self._qdrant.client.upsert(collection_name=self._settings.QDRANT_COLLECTION, points=[point])
        except Exception as exc:  # noqa: BLE001
            raise ExternalServiceError(f"Qdrant upsert failed: {exc}") from exc

    def delete(self, faq_id: str) -> None:
        try:
            self._qdrant.client.delete(
                collection_name=self._settings.QDRANT_COLLECTION,
                points_selector=qmodels.PointIdsList(points=[faq_id]),
            )
        except Exception as exc:  # noqa: BLE001
            raise ExternalServiceError(f"Qdrant delete failed: {exc}") from exc

    def search_similar(self, vector: list[float], limit: int) -> list[dict[str, Any]]:
        try:
            results = self._qdrant.client.search(
                collection_name=self._settings.QDRANT_COLLECTION,
                query_vector=vector,
                limit=limit,
                with_payload=True,
            )
            items: list[dict[str, Any]] = []
            for r in results:
                payload = dict(r.payload or {})
                payload["_score"] = float(r.score)
                payload["_id"] = str(r.id)
                items.append(payload)
            return items
        except Exception as exc:  # noqa: BLE001
            raise ExternalServiceError(f"Qdrant search failed: {exc}") from exc

