from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api import api_router
from app.api.error_handlers import register_error_handlers
from app.api.dependencies import _get_qdrant


def create_app() -> FastAPI:
    app = FastAPI(title="RAG Chatbot Backend", version="1.0.0")
    app.include_router(api_router)
    register_error_handlers(app)

    @app.on_event("startup")
    def _startup() -> None:
        try:
            _get_qdrant().create_collection_if_not_exists()
        except Exception as exc:  # noqa: BLE001
            logging.getLogger(__name__).warning("Qdrant init failed: %s", exc)

    return app


app = create_app()
