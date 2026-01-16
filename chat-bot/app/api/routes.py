from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_chat_service, get_faq_service, get_sync_service
from app.models.schemas import ChatRequest, ChatResponse, FAQCreate, FAQResponse, FAQUpdate, SyncResponse
from app.services.chat_service import ChatService
from app.services.faq_service import FAQService
from app.services.sync_service import SyncService


router = APIRouter(prefix="/api/v1")


@router.post("/faqs", status_code=status.HTTP_201_CREATED)
def create_faq(payload: FAQCreate, service: FAQService = Depends(get_faq_service)) -> dict[str, str]:
    faq_id = service.create_faq(payload)
    return {"id": faq_id}


@router.get("/faqs", response_model=list[FAQResponse])
def list_faqs(service: FAQService = Depends(get_faq_service)) -> list[FAQResponse]:
    return service.list_faqs()


@router.patch("/faqs/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_faq(faq_id: str, payload: FAQUpdate, service: FAQService = Depends(get_faq_service)) -> None:
    service.update_faq(faq_id, payload)
    return None


@router.delete("/faqs/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faq(faq_id: str, service: FAQService = Depends(get_faq_service)) -> None:
    service.delete_faq(faq_id)
    return None


@router.post("/sync", response_model=SyncResponse)
def sync_index(service: SyncService = Depends(get_sync_service)) -> SyncResponse:
    indexed = service.run_full_sync()
    return SyncResponse(indexed=indexed)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, service: ChatService = Depends(get_chat_service)) -> ChatResponse:
    return service.chat(payload.message)

