from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo import MongoClient

from app.config import Settings


class FAQRepository:
    def __init__(self, settings: Settings) -> None:
        self._client = MongoClient(settings.MONGO_URI)
        self._db = self._client[settings.MONGO_DB_NAME]
        self._collection = self._db[settings.MONGO_FAQ_COLLECTION]

    def create(self, faq: dict[str, Any]) -> str:
        result = self._collection.insert_one(dict(faq))
        return str(result.inserted_id)

    def get_by_id(self, faq_id: str) -> dict[str, Any] | None:
        doc = self._collection.find_one({"_id": ObjectId(faq_id)})
        return doc

    def update(self, faq_id: str, data: dict[str, Any]) -> bool:
        result = self._collection.update_one({"_id": ObjectId(faq_id)}, {"$set": dict(data)})
        return result.matched_count > 0

    def delete(self, faq_id: str) -> bool:
        result = self._collection.delete_one({"_id": ObjectId(faq_id)})
        return result.deleted_count > 0

    def get_all(self) -> list[dict[str, Any]]:
        return list(self._collection.find({}))

