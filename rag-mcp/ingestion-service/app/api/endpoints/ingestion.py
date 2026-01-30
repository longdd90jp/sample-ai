from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.schemas.faq import FAQRecord
from app.services.ingestion import ingest_records, ingest_raw

router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Accept JSON files containing Q&A records.
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    content = await file.read()
    try:
        raw = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="Only UTF-8 text files are supported") from exc

    return ingest_raw(raw, file.filename, settings.qdrant_batch_size)


@router.post("/upsert")
async def upsert(records: List[FAQRecord]):
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    payloads = [record.dict() for record in records]
    return ingest_records(payloads, settings.qdrant_batch_size)
