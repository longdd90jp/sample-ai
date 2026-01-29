from typing import Dict, Iterable, List, Tuple


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_record(record: Dict[str, str]) -> Dict[str, str]:
    return {k: normalize_text(v) for k, v in record.items()}


def dedupe_records(records: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    seen: set[Tuple[str, str, str, str]] = set()
    unique: List[Dict[str, str]] = []
    for record in records:
        key = (
            record.get("category", ""),
            record.get("question", ""),
            record.get("answer", ""),
            record.get("source", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique
