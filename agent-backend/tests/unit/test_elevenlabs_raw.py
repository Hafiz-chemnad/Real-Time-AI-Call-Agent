# test_elevenlabs_raw.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
voice_id = os.getenv("ELEVENLABS_VOICE_ID")

url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

headers = {
    "xi-api-key": api_key,
    "Content-Type": "application/json",
}

payload = {
    "text": "Hello, this is a test.",
    "model_id": "eleven_turbo_v2_5",
    "output_format": "pcm_8000",
}

resp = requests.post(url, headers=headers, json=payload, params={"output_format": "pcm_8000"})

print(f"Status: {resp.status_code}")
print(f"Body: {resp.text[:1000]}")