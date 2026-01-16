from __future__ import annotations

from functools import lru_cache

from app.clients.azure_openai import AzureOpenAIClient
from app.clients.qdrant import QdrantClientWrapper
from app.config import Settings, get_settings
from app.repositories.faq_repository import FAQRepository
from app.repositories.vector_repository import VectorRepository
from app.services.chat_service import ChatService
from app.services.faq_service import FAQService
from app.services.sync_service import SyncService


@lru_cache(maxsize=1)
def _get_settings_cached() -> Settings:
    return get_settings()


@lru_cache(maxsize=1)
def _get_faq_repo() -> FAQRepository:
    return FAQRepository(_get_settings_cached())


@lru_cache(maxsize=1)
def _get_openai_client() -> AzureOpenAIClient:
    return AzureOpenAIClient(_get_settings_cached())


@lru_cache(maxsize=1)
def _get_qdrant() -> QdrantClientWrapper:
    return QdrantClientWrapper(_get_settings_cached())


@lru_cache(maxsize=1)
def _get_vector_repo() -> VectorRepository:
    settings = _get_settings_cached()
    return VectorRepository(settings, _get_qdrant())


def get_faq_service() -> FAQService:
    return FAQService(_get_faq_repo(), vector_repo=_get_vector_repo())


def get_sync_service() -> SyncService:
    settings = _get_settings_cached()
    return SyncService(settings, _get_faq_repo(), _get_openai_client(), _get_qdrant(), _get_vector_repo())


def get_chat_service() -> ChatService:
    settings = _get_settings_cached()
    return ChatService(settings, _get_openai_client(), _get_vector_repo())

