from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import torch
from fastapi import FastAPI, HTTPException, Request
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from .model import GenerateRequest, GenerateResponse

BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def _latest_checkpoint(output_dir: Path) -> Path | None:
    # Pick the newest checkpoint-* folder if it exists.
    checkpoints = list(output_dir.glob("checkpoint-*"))
    if not checkpoints:
        return None
    return max(checkpoints, key=lambda p: int(p.name.split("-")[-1]))


def _resolve_model_paths() -> tuple[Path, Path]:
    # Resolve paths relative to fine-tune-pc/ so API works from app/api/.
    root_dir = Path(__file__).resolve().parents[2]
    print(root_dir)
    merged_dir = root_dir / "server-ai" / "merged-model"
    output_dir = root_dir / "server-ai" / "output"
    return merged_dir, output_dir


def _load_model() -> tuple[Any, Any]:
    # Load either a merged model or a base model + LoRA adapter checkpoint.
    merged_dir, output_dir = _resolve_model_paths()

    if merged_dir.exists():
        tokenizer = AutoTokenizer.from_pretrained(merged_dir)
        model = AutoModelForCausalLM.from_pretrained(
            merged_dir,
            torch_dtype=torch.float16,
            device_map="auto",
        )
    else:
        checkpoint = _latest_checkpoint(output_dir) or output_dir
        if not checkpoint.exists():
            raise FileNotFoundError(
                "No fine-tune output found. Train first or provide ./merged-model."
            )
        print("Done loading checkpoint")
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        print("Done loading bnb config")
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=bnb_config,
            device_map="auto",
        )
        print("Done loading base model")
        model = PeftModel.from_pretrained(base_model, checkpoint)
        print("Done loading model")
    model.eval()
    return tokenizer, model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once at startup and reuse for all requests.
    tokenizer, model = _load_model()
    print("Done loading model")
    app.state.tokenizer = tokenizer
    app.state.model = model
    try:
        yield
    finally:
        app.state.tokenizer = None
        app.state.model = None


app = FastAPI(title="Qwen Fine-tune API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest, request: Request) -> GenerateResponse:
    # Use the same chat template as the training/inference script.
    model = request.app.state.model
    tokenizer = request.app.state.tokenizer
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    specs_json = json.dumps(
        [spec.model_dump() for spec in payload.content.specs],
        ensure_ascii=True,
        indent=2,
    )
    prompt = f"Specs:\n{specs_json}\n\nTarget: {payload.content.target}"

    messages = [{"role": "user", "content": prompt}]
    chat_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(chat_prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
            do_sample=True,
        )

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return GenerateResponse(text=text)
