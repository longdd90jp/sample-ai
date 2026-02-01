# Ingestion pipeline for FAQ records into Qdrant.
# Flow: validate -> dedupe -> embed -> upsert.
import json
from typing import Any, Dict, Iterable, List, Tuple

from app.core.utils import dedupe_records, normalize_record
from app.repositories.vector_store import QdrantStore
from app.services.embeddings import get_embedding_client

REQUIRED_FIELDS = ("doc_id", "question", "answer")


def parse_json_records(raw: str) -> List[Dict[str, Any]]:
    """Parse a JSON object/array string into a list of records."""
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError("JSON input must be an object or array")


def parse_jsonl_records(raw: str) -> List[Dict[str, Any]]:
    """Parse a JSONL string into a list of records."""
    records: List[Dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def validate_records(
    records: Iterable[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (valid, invalid) after normalization and required-field checks."""
    valid: List[Dict[str, Any]] = []
    invalid: List[Dict[str, Any]] = []
    for record in records:
        if not all(field in record and isinstance(record[field], str) for field in REQUIRED_FIELDS):
            invalid.append(record)
            continue
        normalized = normalize_record(
            {
                "doc_id": record["doc_id"],
                "question": record["question"],
                "answer": record["answer"],
            }
        )
        metadata = record.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {"metadata": str(metadata)}
        normalized["metadata"] = metadata
        valid.append(normalized)
    return valid, invalid


def load_records(raw: str, filename: str) -> List[Dict[str, Any]]:
    """Load records from JSON or JSONL based on filename extension."""
    if filename.endswith(".jsonl"):
        return parse_jsonl_records(raw)
    return parse_json_records(raw)


def ingest_records(records: List[Dict[str, Any]], batch_size: int) -> Dict[str, Any]:
    """Validate, dedupe, embed, and upsert records into Qdrant."""
    valid, invalid = validate_records(records)
    unique = dedupe_records(valid)

    embedder = get_embedding_client()
    qdrant = QdrantStore()

    ids: List[str] = []

    # Batch embedding + upsert for better throughput.
    for i in range(0, len(unique), batch_size):
        batch = unique[i : i + batch_size]
        doc_ids = [item["doc_id"] for item in batch]
        question_texts = [item["question"] for item in batch]
        answer_texts = [item["answer"] for item in batch]

        # Embed questions and answers into separate named vectors.
        question_vectors = embedder.embed_texts(question_texts)
        answer_vectors = embedder.embed_texts(answer_texts)
        ids.extend(qdrant.upsert_records(doc_ids, question_vectors, answer_vectors))

    return {
        "received": len(records),
        "valid": len(valid),
        "invalid": len(invalid),
        "inserted": len(ids),
        "ids": ids,
    }


def ingest_raw(raw: str, filename: str, batch_size: int) -> Dict[str, Any]:
    """Load records from raw text and ingest them into Qdrant."""
    records = load_records(raw, filename)
    return ingest_records(records, batch_size)


def delete_records(doc_ids: List[str]) -> Dict[str, Any]:
    """Delete records from Qdrant by doc_id."""
    if not doc_ids:
        return {"deleted": 0}
    qdrant = QdrantStore()
    deleted = qdrant.delete_records(doc_ids)
    return {"deleted": deleted}
