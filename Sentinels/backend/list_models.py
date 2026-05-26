import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("XAI_API_KEY") or os.environ.get("GROQ_API_KEY")
url = "https://api.x.ai/v1/models"
resp = requests.get(url, headers={"Authorization": f"Bearer {key}"})
print(resp.status_code)
print(resp.text)
