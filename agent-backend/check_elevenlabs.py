# check_elevenlabs.py
import os
import sys
import requests
from dotenv import load_dotenv

# Force the script to read the new key from .env!
load_dotenv(override=True)
api_key = os.getenv("ELEVENLABS_API_KEY")

if not api_key:
    print("❌ ERROR: ELEVENLABS_API_KEY is missing!")
    sys.exit(1)

masked_key = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
print(f"🔍 Checking ElevenLabs API Key: {masked_key}")

response = requests.get(
    "https://api.elevenlabs.io/v1/user",
    headers={"xi-api-key": api_key}
)

if response.status_code == 200:
    data = response.json()
    print("\n✅ SUCCESS! Your API key is valid and has full permissions.")
    print(f"Tier: {data['subscription']['tier']}")
    
    used = data['subscription']['character_count']
    limit = data['subscription']['character_limit']
    print(f"Characters Used: {used} / {limit}")
    
    if used >= limit:
        print("\n⚠️ ALERT: YOU ARE OUT OF CREDITS!")
        print("ElevenLabs is instantly closing the WebSocket because your account has 0 characters left.")
    else:
        print("\n✅ You have characters remaining. The issue is something else!")
else:
    print("\n❌ FAILED! ElevenLabs rejected the key.")
    print(f"Status Code: {response.status_code}")
    print(f"Error Message: {response.text}")