from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Mongo
    MONGO_URI: str = Field(..., description="MongoDB connection string")
    MONGO_DB_NAME: str = Field("chatbot_db")
    MONGO_FAQ_COLLECTION: str = Field("faqs")

    # Qdrant
    QDRANT_URL: str = Field("http://localhost:6333")
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = Field("faqs")
    QDRANT_VECTOR_SIZE: int = Field(3072, description="Embedding dimension size")
    QDRANT_SEARCH_LIMIT: int = Field(5)

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = Field(..., description="Azure OpenAI API key")
    AZURE_OPENAI_ENDPOINT: str = Field(..., description="Azure OpenAI endpoint")
    AZURE_OPENAI_API_VERSION: str = Field("2023-05-15")
    AZURE_DEPLOYMENT_EMBEDDING: str = Field(..., description="Azure OpenAI embedding deployment name")
    AZURE_DEPLOYMENT_CHAT: str = Field(..., description="Azure OpenAI chat deployment name")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

