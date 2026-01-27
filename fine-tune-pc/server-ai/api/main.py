from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .chat_api import router as chat_router
from .home_api import router as home_router
from .load_model_logic import load_base_model, load_model

# BASE OR FINE_TUNE
MODEL_MODE = "BASE"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once at startup and reuse for all requests.
    if MODEL_MODE == "BASE":
        print("Loading base model")
        tokenizer, model = load_base_model()
    else:
        print("Loading fine-tune model")
        tokenizer, model = load_model()
    print("Done loading model")
    app.state.tokenizer = tokenizer
    app.state.model = model
    try:
        yield
    finally:
        app.state.tokenizer = None
        app.state.model = None


app = FastAPI(title="Qwen Fine-tune API", version="1.0.0", lifespan=lifespan)
app.include_router(home_router)
app.include_router(chat_router)
