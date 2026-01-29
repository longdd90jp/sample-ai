from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, Filter, FieldCondition, MatchValue, PointStruct, VectorParams

from config import settings


class QdrantStore:
    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)

    def ensure_collection(self, vector_size: int) -> None:
        # Lazily create collection with the correct vector size.
        collections = self.client.get_collections().collections
        if any(c.name == settings.qdrant_collection for c in collections):
            return
        self.client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def upsert_records(self, vectors: Iterable[List[float]], payloads: Iterable[Dict[str, Any]]) -> List[str]:
        vectors_list = list(vectors)
        payload_list = list(payloads)
        if not vectors_list:
            return []
        self.ensure_collection(len(vectors_list[0]))

        ids: List[str] = []
        points: List[PointStruct] = []
        for vector, payload in zip(vectors_list, payload_list):
            point_id = str(uuid4())
            ids.append(point_id)
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

        self.client.upsert(collection_name=settings.qdrant_collection, points=points)
        return ids

    def search(self, query_vector: List[float], top_k: int, category: Optional[str] = None):
        query_filter = None
        if category:
            query_filter = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value=category))]
            )
        return self.client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
            query_filter=query_filter,
        )
