import json
from typing import Any, Dict, Iterable, List, Tuple

from embeddings import EmbeddingClient
from qdrant_client import QdrantStore
from utils import dedupe_records, normalize_record

REQUIRED_FIELDS = ("category", "question", "answer")


def build_embedding_text(record: Dict[str, str]) -> str:
    return (
        f"Category: {record['category']}\n"
        f"Question: {record['question']}\n"
        f"Answer: {record['answer']}"
    )


def parse_json_records(raw: str) -> List[Dict[str, Any]]:
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError("JSON input must be an object or array")


def parse_jsonl_records(raw: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def validate_records(records: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    valid: List[Dict[str, str]] = []
    invalid: List[Dict[str, Any]] = []
    for record in records:
        if not all(field in record and isinstance(record[field], str) for field in REQUIRED_FIELDS):
            invalid.append(record)
            continue
        normalized = normalize_record(
            {
                "category": record["category"],
                "question": record["question"],
                "answer": record["answer"],
                "source": str(record.get("source", "ingestion")),
            }
        )
        valid.append(normalized)
    return valid, invalid


def load_records(raw: str, filename: str) -> List[Dict[str, Any]]:
    if filename.endswith(".jsonl"):
        return parse_jsonl_records(raw)
    return parse_json_records(raw)


def ingest_records(raw: str, filename: str, batch_size: int) -> Dict[str, Any]:
    records = load_records(raw, filename)
    valid, invalid = validate_records(records)
    unique = dedupe_records(valid)

    embedder = EmbeddingClient()
    store = QdrantStore()

    ids: List[str] = []
    # Batch embedding + upsert for better throughput.
    for i in range(0, len(unique), batch_size):
        batch = unique[i : i + batch_size]
        texts = [build_embedding_text(item) for item in batch]
        vectors = embedder.embed_texts(texts)
        payloads = [
            {
                "category": item["category"],
                "question": item["question"],
                "answer": item["answer"],
                "source": item["source"],
            }
            for item in batch
        ]
        ids.extend(store.upsert_records(vectors, payloads))

    return {
        "received": len(records),
        "valid": len(valid),
        "invalid": len(invalid),
        "inserted": len(ids),
        "ids": ids,
    }
