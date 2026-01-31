import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")

        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION", "vi_faqs")
        self.question_vector_name = os.getenv("QUESTION_VECTOR_NAME", "question_vector")
        self.answer_vector_name = os.getenv("ANSWER_VECTOR_NAME", "answer_vector")

        self.search_top_k = int(os.getenv("SEARCH_TOP_K", "3"))
        self.search_threshold = float(os.getenv("SEARCH_THRESHOLD", "0.82"))

        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.mongo_db = os.getenv("MONGO_DB", "faq_db")
        self.mongo_collection = os.getenv("MONGO_COLLECTION", "faq_records")


settings = Settings()
