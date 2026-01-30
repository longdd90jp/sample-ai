from typing import Any, Dict, Iterable, List, Optional

from pymongo import MongoClient, UpdateOne

from config import settings


class MongoStore:
    def __init__(self) -> None:
        self.client = MongoClient(settings.mongo_uri)
        self.collection = self.client[settings.mongo_db][settings.mongo_collection]

    def upsert_many(self, records: Iterable[Dict[str, Any]]) -> int:
        operations = []
        for record in records:
            doc_id = record["doc_id"]
            payload = dict(record)
            operations.append(
                UpdateOne({"doc_id": doc_id}, {"$set": payload}, upsert=True)
            )
        if not operations:
            return 0
        result = self.collection.bulk_write(operations, ordered=False)
        return result.upserted_count + result.modified_count + result.matched_count

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        document = self.collection.find_one({"_id": doc_id}, {"_id": 0})
        return document

    def get_by_doc_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        document = self.collection.find_one({"doc_id": doc_id}, {"_id": 0})
        return document

    def get_by_doc_ids(self, doc_ids: Iterable[str]) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"doc_id": {"$in": list(doc_ids)}}, {"_id": 0})
        return list(cursor)
