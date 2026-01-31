from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.repositories.mongo_store import MongoStore
from app.repositories.vector_store import QdrantStore
from app.services.embeddings import get_embedding_client


class SearchService:
    def __init__(self) -> None:
        self.embedder = get_embedding_client()
        self.qdrant = QdrantStore()
        self.mongo = MongoStore()

    def search(self, query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        query_vector = self.embedder.embed_texts([query])[0]

        question_hits = self.qdrant.search(
            query_vector=query_vector,
            top_k=1,
            vector_name=settings.question_vector_name,
        )
        if question_hits:
            top_hit = question_hits[0]
            if top_hit.score >= settings.search_threshold:
                doc_id = (top_hit.payload or {}).get("doc_id")
                document = self.mongo.get_by_id(doc_id) if doc_id else None
                return {
                    "mode": "direct_answer",
                    "doc_id": doc_id,
                    "question": (document or {}).get("question", ""),
                    "answer": (document or {}).get("answer", ""),
                    "score": top_hit.score,
                }

        fallback_k = top_k or settings.search_top_k
        answer_hits = self.qdrant.search(
            query_vector=query_vector,
            top_k=fallback_k,
            vector_name=settings.answer_vector_name,
        )
        doc_ids = [((hit.payload or {}).get("doc_id")) for hit in answer_hits]
        docs = self.mongo.get_by_ids([doc_id for doc_id in doc_ids if doc_id])
        docs_by_id = {doc["doc_id"]: doc for doc in docs if "doc_id" in doc}

        suggestions: List[Dict[str, Any]] = []
        for hit in answer_hits:
            doc_id = (hit.payload or {}).get("doc_id")
            document = docs_by_id.get(doc_id, {})
            if not document:
                continue
            suggestions.append(
                {
                    "doc_id": doc_id,
                    "question": document.get("question", ""),
                    "score": hit.score,
                }
            )

        return {"mode": "suggest_questions", "suggestions": suggestions}
