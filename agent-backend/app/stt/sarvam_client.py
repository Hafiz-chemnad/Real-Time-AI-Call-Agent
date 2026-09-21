import os
import logging

from pipecat.services.sarvam.stt import SarvamSTTService

logger = logging.getLogger(__name__)


def build_sarvam_stt_service() -> SarvamSTTService:
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in .env")

    masked_key = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
    print(f"\n🎧 Authenticating with Sarvam STT Key: {masked_key}")

    stt_service = SarvamSTTService(
        api_key=api_key,
        mode="codemix",       # handles Malayalam + English mixed speech
        sample_rate=16000,    # Synced to 16000 to match Pipecat's internal Twilio VAD workaround[cite: 11]
        settings=SarvamSTTService.Settings(model="saaras:v3"),  
    )

    logger.info("SarvamSTTService initialized (mode=codemix, sample_rate=16000, model=saaras:v3)")
    return stt_service