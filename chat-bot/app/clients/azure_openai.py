from __future__ import annotations

from typing import Any

from openai import AzureOpenAI

from app.config import Settings
from app.core import ExternalServiceError


class AzureOpenAIClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )

    def embed_text(self, text: str) -> list[float]:
        try:
            resp = self._client.embeddings.create(
                model=self._settings.AZURE_DEPLOYMENT_EMBEDDING,
                input=text,
            )
            return list(resp.data[0].embedding)
        except Exception as exc:  # noqa: BLE001
            raise ExternalServiceError(f"Embedding failed: {exc}") from exc

    def generate_chat_response(self, messages: list[dict[str, Any]]) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self._settings.AZURE_DEPLOYMENT_CHAT,
                messages=messages,
                temperature=0.2,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001
            raise ExternalServiceError(f"Chat completion failed: {exc}") from exc

