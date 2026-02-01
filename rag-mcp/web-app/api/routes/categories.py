from typing import List

from fastapi import APIRouter, HTTPException, status
from bson import ObjectId

from ..database import categories_collection
from ..models import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


def serialize_category(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/", response_model=List[CategoryOut])
async def list_categories():
    cursor = categories_collection().find()
    results = [serialize_category(doc) async for doc in cursor]
    return results


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate):
    doc = payload.dict()
    result = await categories_collection().insert_one(doc)
    created = await categories_collection().find_one({"_id": result.inserted_id})
    return serialize_category(created)


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(category_id: str, payload: CategoryUpdate):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid category id")
    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")
    result = await categories_collection().update_one(
        {"_id": ObjectId(category_id)}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    updated = await categories_collection().find_one({"_id": ObjectId(category_id)})
    return serialize_category(updated)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid category id")
    result = await categories_collection().delete_one({"_id": ObjectId(category_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return None
