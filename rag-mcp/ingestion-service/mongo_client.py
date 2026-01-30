from typing import Any, Dict, Iterable, List, Optional

from pymongo import MongoClient, UpdateOne
from bson import ObjectId

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

    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        document = self.collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
        return document

    def get_by_doc_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        document = self.collection.find_one({"doc_id": doc_id}, {"_id": 0})
        return document

    def get_by_doc_ids(self, doc_ids: Iterable[str]) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"doc_id": {"$in": list(doc_ids)}}, {"_id": 0})
        return list(cursor)

    def get_by_ids(self, ids: Iterable[str]) -> List[Dict[str, Any]]:
        object_ids = []
        for value in ids:
            try:
                object_ids.append(ObjectId(value))
            except Exception:
                continue
        if not object_ids:
            return []
        cursor = self.collection.find({"_id": {"$in": object_ids}}, {"_id": 0})
        return list(cursor)
