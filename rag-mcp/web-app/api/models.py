from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None


class CategoryOut(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class QuestionCreate(BaseModel):
    cate_id: str
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class QuestionUpdate(BaseModel):
    cate_id: Optional[str] = None
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = Field(None, min_length=1)


class QuestionOut(BaseModel):
    id: str = Field(alias="_id")
    cate_id: str
    question: str
    answer: str
    created_at: datetime

    class Config:
        allow_population_by_field_name = True