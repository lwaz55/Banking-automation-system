import os
from app.agents.llm_client import generate_completion

# Mock environment
os.environ["GROQ_API_KEY"] = "YOUR_API_KEY"

print("Testing generate_completion with exhausted xAI key...")
result = generate_completion("Say hello", "You are a helpful assistant.")
print(f"Result: {result}")
