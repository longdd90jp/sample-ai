# Technical Implementation Plan - RAG Chatbot Backend

## 1. Project Structure

The project will follow a layered architecture.

```text
chat-bot/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py      # Dependency injection (e.g., get_service)
│   │   ├── routes.py            # API definitions (FAQs, Chat, Sync)
│   │   └── error_handlers.py    # Global exception handlers
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── azure_openai.py      # Wrapper for Azure OpenAI (Embedding & Chat)
│   │   └── qdrant.py            # Wrapper for Qdrant client
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Pydantic BaseSettings management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── domain.py            # Internal domain models (if needed)
│   │   └── schemas.py           # Pydantic DTOs for API requests/responses
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── faq_repository.py    # MongoDB interactions for CRUD
│   │   └── vector_repository.py # Qdrant interactions for Search/Upsert
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py      # RAG logic (Search + Generate)
│   │   ├── faq_service.py       # CRUD logic
│   │   └── sync_service.py      # Embedding generation and syncing logic
│   └── main.py                  # App entrypoint, FastAPI app creation
├── scripts/
│   ├── __init__.py
│   └── reindex.py               # Standalone script for re-indexing
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 2. Layer Responsibilities

### Config (`app/config`)
-   **Responsibility**: Load environment variables.
-   **Implementation**: Use `pydantic-settings`.
-   **Variables**:
    -   `MONGO_URI`, `MONGO_DB_NAME`
    -   `QDRANT_URL`, `QDRANT_API_KEY` (if needed)
    -   `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`
    -   `AZURE_DEPLOYMENT_EMBEDDING`, `AZURE_DEPLOYMENT_CHAT`

### Models (`app/models`)
-   **Responsibility**: Define data contracts (DTOs).
-   **Implementation**: Pydantic models.
-   **Entities**:
    -   `FAQCreate`, `FAQUpdate`, `FAQResponse`
    -   `ChatRequest`, `ChatResponse`
    -   `Category` (embedded in FAQ or separate, based on complexity. Assuming simple string or ID reference for now).

### Clients (`app/clients`)
-   **Responsibility**: Handle low-level communication with external tools.
-   **AzureOpenAIClient**:
    -   `embed_text(text: str) -> List[float]`
    -   `generate_chat_response(messages: List[dict]) -> str`
-   **QdrantClientWrapper**:
    -   `upsert_points(points: List[PointStruct])`
    -   `search(vector: List[float], limit: int) -> List[ScoredPoint]`
    -   `create_collection_if_not_exists()`

### Repositories (`app/repositories`)
-   **Responsibility**: Abstract data access.
-   **FAQRepository** (MongoDB):
    -   `create(faq: dict) -> str`
    -   `get_by_id(id: str) -> dict`
    -   `update(id: str, data: dict)`
    -   `delete(id: str)`
    -   `get_all() -> List[dict]` (Stream or paginated)
-   **VectorRepository** (Qdrant via Client):
    -   `upsert_faq_vector(id: str, vector: List[float], metadata: dict)`
    -   `search_similar(vector: List[float]) -> List[dict]`

### Services (`app/services`)
-   **Responsibility**: Business logic glue.
-   **FAQService**:
    -   Validates input.
    -   Calls `FAQRepository`.
-   **SyncService**:
    -   Orchestrate re-indexing.
    -   Fetch all FAQs from `FAQRepository`.
    -   For each batch:
        -   Generate embeddings via `AzureOpenAIClient`.
        -   Upsert to `VectorRepository`.
-   **ChatService**:
    -   Receive user query.
    -   Generate query embedding (`AzureOpenAIClient`).
    -   Search relevant FAQs (`VectorRepository`).
    -   Construct prompt with context.
    -   Get response (`AzureOpenAIClient`).

### API (`app/api`)
-   **Responsibility**: Handle HTTP requests, parse inputs, return responses, handle errors.
-   **Endpoints**: Delegate strictly to Services.

## 3. Data Flow

### 3.1 FAQ Management (CRUD)
1.  **Request**: `POST /faqs`
2.  **API**: Validates `FAQCreate` schema.
3.  **Service**: `FAQService.create_faq(...)`
4.  **Repo**: `FAQRepository.insert_one(...)` (MongoDB)
5.  **Return**: Created FAQ ID.

### 3.2 Syncing/Re-indexing (RAG Prep)
1.  **Trigger**: `POST /sync` or `python scripts/reindex.py`
2.  **Service**: `SyncService.run_full_sync()`
3.  **Step A**: Fetch all active FAQs from MongoDB.
4.  **Step B**: Loop through FAQs.
    -   Concat `question` + `answer` (or just question, depending on design).
    -   Call `AzureOpenAIClient.embed_text()`.
5.  **Step C**: Call `VectorRepository.upsert(...)` to Qdrant.
    -   Qdrant Point ID should deterministically map to MongoDB ID (or use UUID).
    -   Payload: `{"question": "...", "answer": "...", "category": "..."}`.

### 3.3 Chat (RAG Flow)
1.  **Request**: `POST /chat` (`{ "message": "How do I reset password?" }`)
2.  **Service**: `ChatService.chat(message)`
3.  **Step A**: `AzureOpenAIClient.embed_text(message)` -> `query_vector`.
4.  **Step B**: `VectorRepository.search(query_vector)`.
    -   Returns list of `ScoredPoint`.
    -   Extract `payload.answer` acting as context.
5.  **Step C**: Construct System Prompt.
    -   "You are a helpful assistant. Use the following context to answer..."
6.  **Step D**: `AzureOpenAIClient.generate_chat_response(...)`.
7.  **Return**: `ChatResponse(answer="...")`.

## 4. API Definition

| Method | Path | Description | Body |
| :--- | :--- | :--- | :--- |
| POST | `/api/v1/faqs` | Create new FAQ | `FAQCreate` |
| GET | `/api/v1/faqs` | List FAQs | - |
| PATCH | `/api/v1/faqs/{id}` | Update FAQ | `FAQUpdate` |
| DELETE | `/api/v1/faqs/{id}` | Delete FAQ | - |
| POST | `/api/v1/sync` | Trigger re-index | - |
| POST | `/api/v1/chat` | Chat with RAG | `ChatRequest` |

## 5. Error Handling Strategy

-   **Exceptions**: Define custom exceptions in `app/core/exceptions.py` (e.g., `EntityNotFound`, `ExternalServiceError`).
-   **Handlers**: In `app/api/error_handlers.py`, register `exception_handler` for FastAPI.
-   **Response**: Always return structured JSON for errors:
    ```json
    {
      "error": {
        "code": "ENTITY_NOT_FOUND",
        "message": "FAQ with id 123 not found"
      }
    }
    ```

## 6. Configuration & Environment

Using `pydantic-settings` to validate execution environment on startup.

```python
class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB_NAME: str = "chatbot_db"
    
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "faqs"

    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"
    AZURE_DEPLOYMENT_EMBEDDING: str
    AZURE_DEPLOYMENT_CHAT: str
```

## 7. Re-indexing / Idempotency Strategy

-   **Qdrant Collection**: Created on app startup if not exists.
-   **IDs**: Use MongoDB `_id` (converted to string/UUID) as Qdrant Point ID.
-   **Updates**: Re-running sync for an existing ID in Qdrant will overwrite the vector and payload (Upsert).
-   **Deletes**: When deleting from MongoDB, must also delete from Qdrant via `VectorRepository.delete(id)`.
