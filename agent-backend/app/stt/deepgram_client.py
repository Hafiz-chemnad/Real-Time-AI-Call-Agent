import os
from dotenv import load_dotenv
from pipecat.services.deepgram.stt import DeepgramSTTService

load_dotenv(override=True)

def is_low_confidence(confidence: float) -> bool:
    return confidence < 0.40

def build_deepgram_stt_service():
    api_key = os.getenv("DEEPGRAM_API_KEY")

    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY is missing")

    masked_key = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
    print(f"\n🎧 Authenticating with Deepgram STT Key: {masked_key}")

    stt_service = DeepgramSTTService(
        api_key=api_key,
        encoding="linear16",      
        sample_rate=16000,        # ✅ MATCH THE WORKAROUND: Listen at 16000Hz
        settings=DeepgramSTTService.Settings(
            model="nova-2-phonecall",
            smart_format=True,
            endpointing=500,
            interim_results=False,  
            # NO vad_events=True (Let Silero VAD do its job now that it's fixed!)
        )
    )

    stt_service._settings.language = "en-US"

    return stt_service