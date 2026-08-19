# app/tts/elevenlabs_client.py
import os
from dotenv import load_dotenv
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

load_dotenv(override=True)

def get_primary_tts_service():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "ecp3DWciuUyW7BYM7II1")

    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is missing from environment variables.")

    masked_key = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
    print(f"\n🔐 Authenticating with ElevenLabs Key: {masked_key}")

    tts_service = ElevenLabsTTSService(
    api_key=api_key,
    output_format="ulaw_8000",   # was pcm_8000 — ElevenLabs docs point to μ-law for Twilio/8kHz specifically
    settings=ElevenLabsTTSService.Settings(
        voice=voice_id,
        model="eleven_turbo_v2_5"
    )
    )

    return tts_service