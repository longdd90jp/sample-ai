import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto"
)

print("Model loaded")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

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

print("Dataset loaded")
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj","v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

print("Lora config loaded")
model = get_peft_model(model, lora_config)
model.config.use_cache = False

print("Model loaded")   
training_args = SFTConfig(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    fp16=False,
    bf16=True,
    gradient_checkpointing=True,
    optim="paged_adamw_8bit",
    logging_steps=10,
    eval_strategy="steps",
    eval_steps=50,
    save_steps=100,
    save_total_limit=2,
    report_to="none",
    max_length=2048
)

print("Training args loaded")
def format_chat(example):
    messages = example.get("messages")
    if not messages:
        return ""
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )

print("Format chat loaded")
trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    args=training_args,
    formatting_func=format_chat,
)

print("Trainer loaded")
trainer.train()
print("Training completed")

model.save_pretrained("./output")
print("Model saved")

