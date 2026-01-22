import os
import time
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    TrainerCallback
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# Model and training knobs can be overridden via environment variables.
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-14B-Instruct")  # Base model ID.
MAX_SEQ_LENGTH = int(os.environ.get("MAX_SEQ_LENGTH", "1536"))  # Max tokens per sample.
PER_DEVICE_TRAIN_BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "1"))  # Micro-batch size.
GRADIENT_ACCUMULATION_STEPS = int(os.environ.get("GRAD_ACCUM", "8"))  # Steps to reach effective batch.

# Prefer BF16 on newer GPUs; fall back to FP16 otherwise.
use_bf16 = (
    torch.cuda.is_available()
    and torch.cuda.get_device_capability(0)[0] >= 8
)
# Enable TF32 matmul for faster training on supported GPUs.
torch.backends.cuda.matmul.allow_tf32 = True
torch.set_float32_matmul_precision("high")

# QLoRA 4-bit quantization config to fit larger models into VRAM.
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,  # 4-bit quantization to reduce VRAM.
    bnb_4bit_quant_type="nf4",  # NF4 gives better accuracy than int4.
    bnb_4bit_compute_dtype=torch.bfloat16 if use_bf16 else torch.float16,  # Compute dtype.
)

# Load base model with 4-bit weights; let HF decide device placement.
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,  # Enable QLoRA weights.
    device_map="auto"  # Auto place layers across available devices.
)

# Load tokenizer and align padding with EOS token for causal LM.
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token  # Avoid undefined pad token.
tokenizer.padding_side = "right"  # Right padding for causal LM.

# Load JSONL chat datasets from local files.
dataset = load_dataset(
    "json",
    data_files={
        "train": [
            "data/training_set_ai.jsonl",
            "data/training_set_coding.jsonl",
            "data/training_set_gamming.jsonl",
            "data/training_set_meeting.jsonl",
            "data/training_set_office.jsonl",
        ],
        "validation": "data/validation_set.jsonl"
    }
)

# LoRA adapter config: inject low-rank matrices into attention projections.
lora_config = LoraConfig(
    r=16,  # LoRA rank: higher = more capacity, more VRAM.
    lora_alpha=32,  # Scaling for LoRA updates.
    target_modules=["q_proj", "v_proj"],  # Attention projections to adapt.
    lora_dropout=0.05,  # Regularization for LoRA layers.
    bias="none",  # Do not train bias terms.
    task_type="CAUSAL_LM"  # Causal language modeling task.
)

# Wrap the model with PEFT adapters and disable cache for training.
model = get_peft_model(model, lora_config)
model.config.use_cache = False

# Standard HF training arguments tuned for QLoRA on limited VRAM.
training_args = TrainingArguments(
    output_dir="./output",  # Checkpoints and logs.
    num_train_epochs=3,  # Full passes over the train set.
    per_device_train_batch_size=PER_DEVICE_TRAIN_BATCH_SIZE,  # Micro-batch per GPU.
    gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,  # Effective batch size.
    learning_rate=2e-4,  # Typical LoRA LR.
    fp16=not use_bf16,  # Mixed precision for speed/VRAM.
    bf16=use_bf16,  # Prefer BF16 on newer GPUs.
    gradient_checkpointing=True,  # Save VRAM by recomputing activations.
    optim="paged_adamw_8bit",  # 8-bit optimizer to save memory.
    group_by_length=True,  # Pack similar lengths for better throughput.
    dataloader_num_workers=max(2, (os.cpu_count() or 4) // 2),  # Use CPU cores.
    dataloader_pin_memory=True,  # Faster host-to-device transfer.
    logging_steps=10,  # Print logs every N steps.
    evaluation_strategy="steps",  # Eval during training.
    eval_steps=50,  # Eval frequency.
    save_steps=100,  # Checkpoint frequency.
    save_total_limit=2,  # Keep only last N checkpoints.
    report_to="none"  # Disable external loggers.
)

# Convert a chat example into a single prompt string.
def format_chat(example):
    messages = example.get("messages")  # Expect a list of role/content messages.
    if not messages:
        return ""
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False  # Train on full chat without assistant prefix.
    )

# Simple throughput/ETA logger based on tokens per step.
class ThroughputCallback(TrainerCallback):
    def __init__(self, tokens_per_step):
        self.tokens_per_step = tokens_per_step
        self.start_time = None
        self.last_step = 0
        self.last_time = None

    def on_train_begin(self, args, state, control, **kwargs):
        # Initialize timers for throughput estimation.
        self.start_time = time.time()
        self.last_time = self.start_time

    def on_log(self, args, state, control, **kwargs):
        if self.start_time is None:
            return
        now = time.time()
        step = state.global_step
        if step <= self.last_step:
            return
        step_delta = step - self.last_step
        time_delta = max(1e-6, now - (self.last_time or now))
        tokens_per_sec = (step_delta * self.tokens_per_step) / time_delta
        if state.max_steps:
            # Estimate remaining time based on recent step speed.
            remaining_steps = max(0, state.max_steps - step)
            remaining_seconds = remaining_steps * (time_delta / step_delta)
            eta_min = remaining_seconds / 60
            print(
                f"[speed] {tokens_per_sec:,.0f} tokens/s | "
                f"step {step}/{state.max_steps} | eta {eta_min:,.1f} min"
            )
        else:
            print(f"[speed] {tokens_per_sec:,.0f} tokens/s | step {step}")
        self.last_step = step
        self.last_time = now

# Build the SFT trainer with formatting and max sequence length.
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    args=training_args,
    formatting_func=format_chat,
    max_seq_length=MAX_SEQ_LENGTH,
)

# Estimate tokens per step for throughput logging.
tokens_per_step = (
    PER_DEVICE_TRAIN_BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS * MAX_SEQ_LENGTH
)
trainer.add_callback(ThroughputCallback(tokens_per_step))

# Start training.
trainer.train()
