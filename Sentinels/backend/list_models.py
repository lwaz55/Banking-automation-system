import requests
key = "YOUR_API_KEY"
url = "https://api.x.ai/v1/models"
resp = requests.get(url, headers={"Authorization": f"Bearer {key}"})
print(resp.status_code)
print(resp.text)
