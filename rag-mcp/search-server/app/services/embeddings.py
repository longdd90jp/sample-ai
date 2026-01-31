from functools import lru_cache
from typing import Iterable, List

from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingClient:
    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.embedding_model_name)
        self.expected_dim = 1024

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        payload = list(texts)
        if not payload:
            return []
        embeddings = self.model.encode(payload, convert_to_numpy=True).tolist()
        if embeddings and len(embeddings[0]) != self.expected_dim:
            raise ValueError(
                f"Unexpected embedding dimension: {len(embeddings[0])} (expected {self.expected_dim})"
            )
        return embeddings


@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    return EmbeddingClient()
