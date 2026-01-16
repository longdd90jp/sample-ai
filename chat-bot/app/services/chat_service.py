from __future__ import annotations

from typing import Any

from app.clients.azure_openai import AzureOpenAIClient
from app.config import Settings
from app.models.schemas import ChatResponse
from app.repositories.vector_repository import VectorRepository


class ChatService:
    def __init__(self, settings: Settings, openai_client: AzureOpenAIClient, vector_repo: VectorRepository) -> None:
        self._settings = settings
        self._openai = openai_client
        self._vectors = vector_repo

    def chat(self, message: str) -> ChatResponse:
        query_vector = self._openai.embed_text(message)
        hits = self._vectors.search_similar(query_vector, limit=self._settings.QDRANT_SEARCH_LIMIT)
        context_lines = []
        for h in hits:
            q = h.get("question", "")
            a = h.get("answer", "")
            score = h.get("_score", 0.0)
            context_lines.append(f"- (score={score:.3f}) Q: {q}\n  A: {a}")
        context = "\n".join(context_lines).strip()

        system_prompt = (
            "You are a helpful assistant. Answer the user using ONLY the provided FAQ context. "
            "If the context does not contain the answer, say you don't know and ask a clarifying question."
        )
        user_content = f"FAQ Context:\n{context or '(empty)'}\n\nUser question: {message}"
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        answer = self._openai.generate_chat_response(messages)
        sources = [
            {
                "id": h.get("_id"),
                "score": h.get("_score"),
                "category_id": h.get("category_id"),
                "question": h.get("question"),
            }
            for h in hits
        ]
        return ChatResponse(answer=answer, sources=sources)

