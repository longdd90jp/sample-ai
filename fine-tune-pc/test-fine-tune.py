from transformers import pipeline

pipe = pipeline(
    "text-generation",
    model="./merged-model",
    tokenizer="./merged-model",
    max_new_tokens=300
)

pipe("Build a PC for office work")
