import os
import requests

from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("XAI_API_KEY") or os.environ.get("GROQ_API_KEY")
url = "https://api.x.ai/v1/chat/completions"

def test_xai(json_mode):
    request_body = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ],
        "temperature": 0.1,
    }
    if json_mode:
        request_body["response_format"] = {"type": "json_object"}
        
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json=request_body
    )
    print(f"json_mode={json_mode}: {resp.status_code}")
    print(resp.text)

test_xai(False)
test_xai(True)
