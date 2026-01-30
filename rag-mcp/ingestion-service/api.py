from typing import List

from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from config import settings
from ingestion import ingest_records, ingest_raw

app = FastAPI(title="ingestion-service")
router = APIRouter(prefix="/api")


class FAQRecord(BaseModel):
    doc_id: str
    question: str
    answer: str
    metadata: Optional[dict] = None


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


app.include_router(router)
