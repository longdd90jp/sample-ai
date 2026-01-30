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

        self.embedding_max_retries = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))
        self.embedding_retry_backoff = float(os.getenv("EMBEDDING_RETRY_BACKOFF", "1.5"))

        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION", "vi_faqs")

        self.embedding_batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
        self.qdrant_batch_size = int(os.getenv("QDRANT_BATCH_SIZE", "64"))
        self.search_top_k = int(os.getenv("SEARCH_TOP_K", "5"))
        self.search_threshold = float(os.getenv("SEARCH_THRESHOLD", "0.82"))
        self.question_vector_name = os.getenv("QUESTION_VECTOR_NAME", "question_vector")
        self.answer_vector_name = os.getenv("ANSWER_VECTOR_NAME", "answer_vector")

        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.mongo_db = os.getenv("MONGO_DB", "faq_db")
        self.mongo_collection = os.getenv("MONGO_COLLECTION", "faq_records")


settings = Settings()
