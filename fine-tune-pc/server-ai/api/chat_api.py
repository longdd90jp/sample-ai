from __future__ import annotations

import json

import torch
from fastapi import APIRouter, HTTPException, Request

from .model import GenerateRequest, GenerateResponse

router = APIRouter()


def _generate_response(payload: GenerateRequest, request: Request) -> GenerateResponse:
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

    messages = [
        {"role": "system", "content": "Bạn là tư vấn viên bán lẻ linh kiện PC chuyên nghiệp."},
        {"role": "user", "content": prompt}
        ]
    chat_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(chat_prompt, return_tensors="pt").to(model.device)
    input_ids = inputs["input_ids"]
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
            do_sample=True,
        )

    # Only decode the newly generated tokens
    generated_ids = outputs[0][len(input_ids[0]) :]
    text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return GenerateResponse(text=text)


@router.post("/api/fine-tune/generate", response_model=GenerateResponse)
def generate_fine_tune(
    payload: GenerateRequest, request: Request
) -> GenerateResponse:
    return _generate_response(payload, request)


@router.post("/api/base/generate", response_model=GenerateResponse)
def generate_base(payload: GenerateRequest, request: Request) -> GenerateResponse:
    return _generate_response(payload, request)
