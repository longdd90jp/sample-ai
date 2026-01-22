from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
MERGED_DIR = Path("./merged-model")
OUTPUT_DIR = Path("./output")

def latest_checkpoint(output_dir: Path) -> Path | None:
    checkpoints = list(output_dir.glob("checkpoint-*"))
    if not checkpoints:
        return None
    return max(checkpoints, key=lambda p: int(p.name.split("-")[-1]))

if MERGED_DIR.exists():
    tokenizer = AutoTokenizer.from_pretrained(MERGED_DIR)
    model = AutoModelForCausalLM.from_pretrained(
        MERGED_DIR,
        torch_dtype=torch.float16,
        device_map="auto"
    )
else:
    checkpoint = latest_checkpoint(OUTPUT_DIR) or OUTPUT_DIR
    if not checkpoint.exists():
        raise FileNotFoundError(
            "No fine-tune output found. Train first or provide ./merged-model."
        )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    model = PeftModel.from_pretrained(base_model, checkpoint)

messages = [
    {"role": "system", "content": "You are a PC consultant."},
    {"role": "user", "content": "Build a PC for office work with low budget."}
]

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=300,
        temperature=0.7,
        top_p=0.9,
        do_sample=True
    )

result = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("\n=== MODEL OUTPUT ===")
print(result)
