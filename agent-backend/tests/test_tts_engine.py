import asyncio
import time
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

from app.tts.tts_engine import TTSEngine


async def run_test(engine, text, number):
    print()
    print(f"===== TEST {number} =====")
    print(f"Text: {text}")

    start = time.perf_counter()
    first_audio = None
    total_bytes = 0
    chunks = 0

    async for audio in engine.synthesize(text):

        if first_audio is None:
            first_audio = time.perf_counter()

            ttfa = (first_audio - start) * 1000

            print(f"FIRST AUDIO: {ttfa:.2f} ms")

        total_bytes += len(audio)
        chunks += 1

    total = (time.perf_counter() - start) * 1000

    print(f"Total time : {total:.2f} ms")
    print(f"Chunks     : {chunks}")
    print(f"Bytes      : {total_bytes}")

    return ttfa


async def main():

    engine = TTSEngine()

    ttfa1 = await run_test(
        engine,
        "Hello, welcome to our AI calling system. How can I help you today?",
        1,
    )

    ttfa2 = await run_test(
        engine,
        "Your appointment has been successfully confirmed for tomorrow at 10 AM.",
        2,
    )

    print()
    print("=" * 45)
    print("TTFA COMPARISON")
    print("=" * 45)
    print(f"First request  : {ttfa1:.2f} ms")
    print(f"Second request : {ttfa2:.2f} ms")
    print("=" * 45)


if __name__ == "__main__":
    asyncio.run(main())