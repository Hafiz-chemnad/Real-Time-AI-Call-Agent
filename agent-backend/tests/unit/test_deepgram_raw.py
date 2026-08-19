# test_deepgram_raw.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEEPGRAM_API_KEY")

url = "https://api.deepgram.com/v1/listen"
params = {
    "model": "nova-3",
    "language": "en",
    "smart_format": "true",
}
headers = {
    "Authorization": f"Token {api_key}",
    "Content-Type": "audio/wav",
}

# Deepgram's own public sample audio file, safe to fetch for testing
sample_audio_url = "https://static.deepgram.com/examples/interview_speech-analytics.wav"
audio_bytes = requests.get(sample_audio_url).content

resp = requests.post(url, headers=headers, params=params, data=audio_bytes)

print(f"Status: {resp.status_code}")
print(f"Body: {resp.text[:1500]}")