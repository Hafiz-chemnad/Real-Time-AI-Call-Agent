# test_deepgram_ws.py
import asyncio
import os
import websockets
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEEPGRAM_API_KEY")

url = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-3&language=en&smart_format=true"
    "&encoding=mulaw&sample_rate=8000"
)

async def main():
    try:
        async with websockets.connect(
            url,
            additional_headers={"Authorization": f"Token {api_key}"},
        ) as ws:
            print("✅ Connected successfully!")
            await ws.close()
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Rejected with status: {e.status_code}")
        print(f"Headers: {e.headers}")
    except Exception as e:
        print(f"❌ Other error: {type(e).__name__}: {e}")

asyncio.run(main())