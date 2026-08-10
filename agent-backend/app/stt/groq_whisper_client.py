import os
import logging

from pipecat.services.groq.stt import GroqSTTService

logger = logging.getLogger(__name__)


def build_groq_stt_service() -> GroqSTTService:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in .env")

    stt_service = GroqSTTService(
        api_key=api_key,
        settings=GroqSTTService.Settings(
            model="whisper-large-v3-turbo"
        ),
    )

    logger.info("GroqSTTService initialized (Tier 2 fallback)")
    return stt_service