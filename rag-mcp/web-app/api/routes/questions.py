from datetime import datetime
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
import httpx
from bson import ObjectId

from ..database import categories_collection, questions_collection
from ..models import QuestionCreate, QuestionUpdate, QuestionOut

router = APIRouter(prefix="/questions", tags=["questions"])

INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8001")


async def upsert_ingestion_record(doc_id: str, question: str, answer: str) -> None:
    payload = [{"doc_id": doc_id, "question": question, "answer": answer}]
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(f"{INGESTION_URL}/api/upsert", json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Ingestion service upsert failed")


async def delete_ingestion_record(doc_id: str) -> None:
    payload = {"doc_ids": [doc_id]}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(f"{INGESTION_URL}/api/delete", json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Ingestion service delete failed")


def serialize_question(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    doc["cate_id"] = str(doc["cate_id"])
    return doc


@router.get("/", response_model=List[QuestionOut])
async def list_questions(cate_id: Optional[str] = None):
    query = {}
    if cate_id:
        if not ObjectId.is_valid(cate_id):
            raise HTTPException(status_code=400, detail="Invalid category id")
        query["cate_id"] = ObjectId(cate_id)
    cursor = questions_collection().find(query).sort("created_at", -1)
    results = [serialize_question(doc) async for doc in cursor]
    return results


@router.post("/", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def create_question(payload: QuestionCreate):
    if not ObjectId.is_valid(payload.cate_id):
        raise HTTPException(status_code=400, detail="Invalid category id")
    category = await categories_collection().find_one({"_id": ObjectId(payload.cate_id)})
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    doc = {
        "cate_id": ObjectId(payload.cate_id),
        "question": payload.question,
        "answer": payload.answer,
        "created_at": datetime.utcnow(),
    }
    result = await questions_collection().insert_one(doc)
    created = await questions_collection().find_one({"_id": result.inserted_id})
    serialized = serialize_question(created)
    await upsert_ingestion_record(
        serialized["_id"], serialized["question"], serialized["answer"]
    )
    return serialized


@router.put("/{question_id}", response_model=QuestionOut)
async def update_question(question_id: str, payload: QuestionUpdate):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="Invalid question id")
    update_data = payload.dict(exclude_unset=True)
    if "cate_id" in update_data:
        if not ObjectId.is_valid(update_data["cate_id"]):
            raise HTTPException(status_code=400, detail="Invalid category id")
        category = await categories_collection().find_one(
            {"_id": ObjectId(update_data["cate_id"])}
        )
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
        update_data["cate_id"] = ObjectId(update_data["cate_id"])
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")
    result = await questions_collection().update_one(
        {"_id": ObjectId(question_id)}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    updated = await questions_collection().find_one({"_id": ObjectId(question_id)})
    serialized = serialize_question(updated)
    await upsert_ingestion_record(
        serialized["_id"], serialized["question"], serialized["answer"]
    )
    return serialized


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: str):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="Invalid question id")
    result = await questions_collection().delete_one({"_id": ObjectId(question_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    await delete_ingestion_record(question_id)
    return None
