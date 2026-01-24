from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

BASE_MODEL = "Qwen/Qwen2.5-14B-Instruct"


def latest_checkpoint(output_dir: Path) -> Path | None:
    # Pick the newest checkpoint-* folder if it exists.
    checkpoints = list(output_dir.glob("checkpoint-*"))
    if not checkpoints:
        return None
    return max(checkpoints, key=lambda p: int(p.name.split("-")[-1]))


def resolve_model_paths() -> tuple[Path, Path]:
    # Resolve paths relative to fine-tune-pc/ so API works from api/.
    root_dir = Path(__file__).resolve().parents[2]
    merged_dir = root_dir / "server-ai" / "merged-model"
    output_dir = root_dir / "server-ai" / "output"
    return merged_dir, output_dir


def _base_bnb_config() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )


def load_base_model() -> tuple[Any, Any]:
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=_base_bnb_config(),
        device_map="auto",
    )
    base_model.eval()
    return tokenizer, base_model


def load_model() -> tuple[Any, Any]:
    # Load either a merged model or a base model + LoRA adapter checkpoint.
    merged_dir, output_dir = resolve_model_paths()

    if merged_dir.exists():
        tokenizer = AutoTokenizer.from_pretrained(merged_dir)
        model = AutoModelForCausalLM.from_pretrained(
            merged_dir,
            torch_dtype=torch.float16,
            device_map="auto",
        )
    else:
        checkpoint = latest_checkpoint(output_dir) or output_dir
        if not checkpoint.exists():
            raise FileNotFoundError(
                "No fine-tune output found. Train first or provide ./merged-model."
            )
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=_base_bnb_config(),
            device_map="auto",
        )
        model = PeftModel.from_pretrained(base_model, checkpoint)

    model.eval()
    return tokenizer, model
