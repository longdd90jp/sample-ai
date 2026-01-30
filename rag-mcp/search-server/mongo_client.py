from typing import Any, Dict, Iterable, List, Optional

from pymongo import MongoClient

from config import settings


class MongoStore:
    def __init__(self) -> None:
        self.client = MongoClient(settings.mongo_uri)
        self.collection = self.client[settings.mongo_db][settings.mongo_collection]

    def get_by_doc_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"doc_id": doc_id}, {"_id": 0})

    def get_by_doc_ids(self, doc_ids: Iterable[str]) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"doc_id": {"$in": list(doc_ids)}}, {"_id": 0})
        return list(cursor)
