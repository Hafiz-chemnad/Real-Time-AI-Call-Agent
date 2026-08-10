import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Find agent-backend/.env explicitly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)

from app.tts.cartesia_client import CartesiaClient


async def main():
    print(f".env path: {ENV_FILE}")
    print(
        "Cartesia API key:",
        "OK" if os.getenv("CARTESIA_API_KEY") else "MISSING"
    )
    print(
        "Cartesia Voice ID:",
        "OK" if os.getenv("CARTESIA_VOICE_ID") else "MISSING"
    )

    client = CartesiaClient()

    print("Connecting to Cartesia...")

    output_file = "tests/cartesia_test.pcm"
    total_bytes = 0

    try:
        with open(output_file, "wb") as file:
            async for audio in client.synthesize_stream(
                "Hello, this is a real time Cartesia TTS test."
            ):
                file.write(audio)
                total_bytes += len(audio)

                print(
                    f"Received audio chunk: {len(audio)} bytes"
                )

        print()
        print("Cartesia TTS completed!")
        print(f"Audio file: {output_file}")
        print(f"Total bytes: {total_bytes}")

    except Exception as error:
        print()
        print("Cartesia TTS failed!")
        print(f"Error: {error}")


if __name__ == "__main__":
    asyncio.run(main())