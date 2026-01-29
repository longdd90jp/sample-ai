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
        # One record -> one vector for Q&A retrieval.
        response = self.client.embeddings.create(
            model=settings.azure_openai_embedding_deployment,
            input=list(texts),
        )
        return [item.embedding for item in response.data]
