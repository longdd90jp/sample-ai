import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_openai_api_version = (
            os.getenv("AZURE_OPENAI_API_VERSION")
            or os.getenv("OPENAI_API_VERSION", "2024-02-01")
        )
        self.azure_openai_embedding_deployment = os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", ""
        )

        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION", "qa_records")

        self.embedding_batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
        self.qdrant_batch_size = int(os.getenv("QDRANT_BATCH_SIZE", "64"))
        self.search_top_k = int(os.getenv("SEARCH_TOP_K", "5"))


settings = Settings()
