import inspect
from typing import Iterable, List, Optional
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings


class QdrantStore:
    """Thin wrapper around Qdrant for FAQ vector storage and search."""

    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)

    def ensure_collection(self, vector_size: int) -> None:
        """Create the collection with named vectors if it does not exist."""
        collections = self.client.get_collections().collections
        if any(c.name == settings.qdrant_collection for c in collections):
            return
        self.client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config={
                settings.question_vector_name: VectorParams(
                    size=vector_size, distance=Distance.COSINE
                ),
                settings.answer_vector_name: VectorParams(
                    size=vector_size, distance=Distance.COSINE
                ),
            },
        )

    def _find_point_id(self, doc_id: str) -> Optional[str]:
        """Return existing point id for a doc_id, if any."""
        query_filter = Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        )
        points, _ = self.client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=query_filter,
            limit=1,
            with_payload=False,
            with_vectors=False,
        )
        if points:
            return str(points[0].id)
        return None

    def upsert_records(
        self,
        doc_ids: Iterable[str],
        question_vectors: Iterable[List[float]],
        answer_vectors: Iterable[List[float]],
    ) -> List[str]:
        """Upsert question/answer vectors keyed by doc_id and return point ids."""
        doc_list = list(doc_ids)
        question_list = list(question_vectors)
        answer_list = list(answer_vectors)
        if not doc_list:
            return []
        self.ensure_collection(len(question_list[0]))

        ids: List[str] = []
        points: List[PointStruct] = []
        for doc_id, q_vector, a_vector in zip(doc_list, question_list, answer_list):
            point_id = self._find_point_id(doc_id) or str(uuid4())
            ids.append(point_id)
            points.append(
                PointStruct(
                    id=point_id,
                    vector={
                        settings.question_vector_name: q_vector,
                        settings.answer_vector_name: a_vector,
                    },
                    payload={"doc_id": doc_id},
                )
            )

        self.client.upsert(collection_name=settings.qdrant_collection, points=points)
        return ids

    def search(
        self,
        query_vector: List[float],
        top_k: int,
        vector_name: str,
    ):
        """Search for nearest vectors using the best available client method."""
        if hasattr(self.client, "search"):
            return self.client.search(
                collection_name=settings.qdrant_collection,
                query_vector=query_vector,
                vector_name=vector_name,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
        params = inspect.signature(self.client.query_points).parameters
        kwargs = {
            "collection_name": settings.qdrant_collection,
            "limit": top_k,
            "with_payload": True,
            "with_vectors": False,
        }
        if "query_vector" in params:
            kwargs["query_vector"] = query_vector
            if "vector_name" in params:
                kwargs["vector_name"] = vector_name
        elif "query" in params:
            kwargs["query"] = query_vector
            if "using" in params:
                kwargs["using"] = vector_name
        else:
            raise AssertionError("Unsupported qdrant-client query_points signature")
        response = self.client.query_points(**kwargs)
        return response.points

    def delete_records(self, doc_ids: Iterable[str]) -> int:
        """Delete points by doc_id payload and return count of delete ops."""
        deleted = 0
        for doc_id in doc_ids:
            query_filter = Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            )
            self.client.delete(
                collection_name=settings.qdrant_collection,
                points_selector=query_filter,
            )
            deleted += 1
        return deleted
