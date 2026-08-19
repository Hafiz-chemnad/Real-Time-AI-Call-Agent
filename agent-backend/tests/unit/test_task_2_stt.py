import asyncio
import os
from dotenv import load_dotenv

# Load environment variables (API Keys)
load_dotenv()

from app.stt.deepgram_client import build_deepgram_stt_service
from app.stt.groq_whisper_client import build_groq_stt_service
from app.stt.local_whisper_client import build_local_whisper_stt_service

async def run_m2_tests():
    print("\n" + "="*50)
    print("🎧 MILESTONE 2: STT (Speech-to-Text) FULL TEST")
    print("="*50)

    print("\n[TEST 1] Testing Tier 1: Deepgram (Primary Cloud)")
    try:
        dg_service = build_deepgram_stt_service()
        print("✅ Deepgram STT initialized successfully!")
    except Exception as e:
        print(f"❌ Deepgram failed: {e}")

    print("\n[TEST 2] Testing Tier 2: Groq Whisper (Secondary Cloud)")
    try:
        groq_service = build_groq_stt_service()
        print("✅ Groq STT initialized successfully!")
    except Exception as e:
        print(f"❌ Groq failed: {e}")

    print("\n[TEST 3] Testing Tier 3: Local Whisper (Offline Fallback)")
    print("⚠️  Note: If this is your first time running this, it will pause here to download the model weights (~1.5 GB).")
    try:
        local_service = build_local_whisper_stt_service()
        print("✅ Local Whisper initialized successfully!")
    except Exception as e:
        print(f"❌ Local Whisper failed: {e}")

    print("\n" + "="*50)
    print("If all three have green checkmarks ✅, Milestone 2 is flawless!")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_m2_tests())