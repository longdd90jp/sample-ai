from functools import lru_cache
from typing import Iterable, List

from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingClient:
    """Embed text locally using the configured sentence-transformers model."""

    def __init__(self) -> None:
        self.model_name = settings.embedding_model_name
        self.expected_dim = 1024
        self.model = SentenceTransformer(self.model_name)

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        """Return a list of embedding vectors for the provided texts."""
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
    print("Loading embedding model...")
    return EmbeddingClient()
