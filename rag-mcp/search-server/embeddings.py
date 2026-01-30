import time
from typing import Iterable, List

from openai import AzureOpenAI

from config import settings


class EmbeddingClient:
    def __init__(self) -> None:
        if not settings.azure_openai_embedding_deployment:
            raise ValueError("Missing AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        payload = list(texts)
        for attempt in range(settings.embedding_max_retries):
            try:
                response = self.client.embeddings.create(
                    model=settings.azure_openai_embedding_deployment,
                    input=payload,
                )
                return [item.embedding for item in response.data]
            except Exception:
                if attempt == settings.embedding_max_retries - 1:
                    raise
                time.sleep(settings.embedding_retry_backoff ** attempt)
        return []
