"""
app/stt/deepgram_client.py

Tier 1 (Primary Cloud) STT client — Deepgram Nova-3, telephony-tuned.
"""

import os
import logging

from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transcriptions.language import Language

logger = logging.getLogger(__name__)


def build_deepgram_stt_service(
    confidence_threshold: float = 0.6,
) -> DeepgramSTTService:
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPGRAM_API_KEY is not set. Add it to your .env file."
        )

    # 1. Pass connection-level audio parameters directly as service kwargs.
    # 2. Pass model options in settings=DeepgramSTTService.Settings(...).
    stt_service = DeepgramSTTService(
        api_key=api_key,
        encoding="mulaw",
        sample_rate=8000,
        channels=1,
        settings=DeepgramSTTService.Settings(
            model="nova-3",
            language=Language.EN,
        ),
    )

    logger.info(
        "DeepgramSTTService initialized (model=nova-3-phonecall, "
        "encoding=mulaw, sample_rate=8000, confidence_threshold=%.2f)",
        confidence_threshold,
    )

    return stt_service


def is_low_confidence(confidence: float, threshold: float = 0.6) -> bool:
    return confidence < threshold