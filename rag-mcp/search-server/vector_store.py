import inspect
from typing import List

from qdrant_client import QdrantClient

from config import settings


class QdrantStore:
    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)

    def search(self, query_vector: List[float], top_k: int, vector_name: str):
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
