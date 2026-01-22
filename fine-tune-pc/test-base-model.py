import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)

messages = [
    {"role": "system", "content": "You are a PC consultant."},
    {"role": "user", "content": "Build a PC for office work with low budget."}
]

# Convert chat → prompt text
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
