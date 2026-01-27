import os
from openai import AzureOpenAI

endpoint = "https://poc-ai-team-fine-tune.openai.azure.com/"
model_name = "gpt-4o-mini"
deployment = "gpt-4o-mini"

subscription_key = "D3nV5XzpE5FdhdhJ44ZRyDU2AavApbUKwkpwM20s0NqdTBfPDrQqJQQJ99CAACHYHv6XJ3w3AAABACOG7iHw"
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "Clippy is a factual chatbot that is also sarcastic.",
        },
        {
            "role": "user",
            "content": "Nước Pháp ở đâu?", # How far is the moon?
        }
    ],
    max_tokens=4096,
    temperature=1.0,
    top_p=1.0,
    model=deployment
)

print(response.choices[0].message.content)