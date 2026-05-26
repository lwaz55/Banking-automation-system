import os
from app.agents.llm_client import generate_completion

from dotenv import load_dotenv

load_dotenv()

print("Testing generate_completion with API key from .env...")
result = generate_completion("Say hello", "You are a helpful assistant.")
print(f"Result: {result}")
