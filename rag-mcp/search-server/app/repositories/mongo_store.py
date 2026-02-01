from typing import Any, Dict, Iterable, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

from app.core.config import settings


class MongoStore:
    def __init__(self) -> None:
        self.client = MongoClient(settings.mongo_uri)
        self.collection = self.client[settings.mongo_db][settings.mongo_collection]

    def get_by_id(self, id_str: str) -> Optional[Dict[str, Any]]:
        try:
            object_id = ObjectId(id_str)
        except (InvalidId, TypeError):
            return None
        doc = self.collection.find_one({"_id": object_id})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return doc

    def get_by_ids(self, id_strs: Iterable[str]) -> List[Dict[str, Any]]:
        object_ids: List[ObjectId] = []
        for id_str in id_strs:
            try:
                object_ids.append(ObjectId(id_str))
            except (InvalidId, TypeError):
                continue
        if not object_ids:
            return []
        cursor = self.collection.find({"_id": {"$in": object_ids}})
        docs: List[Dict[str, Any]] = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            docs.append(doc)
        return docs
