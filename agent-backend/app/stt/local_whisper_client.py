"""
app/stt/local_whisper_client.py

Tier 3 (Local Offline Fallback) STT client — faster-whisper running
locally via Pipecat's native WhisperSTTService.
"""

import logging

from pipecat.services.whisper.stt import WhisperSTTService, Model
from pipecat.transcriptions.language import Language

logger = logging.getLogger(__name__)


def build_local_whisper_stt_service(
    model: Model = Model.DISTIL_MEDIUM_EN,
    device: str = "cpu",
    compute_type: str = "int8",
) -> WhisperSTTService:
    
    # Modern Pipecat 0.0.107 syntax: Use Settings() for model config
    stt_service = WhisperSTTService(
        device=device,
        compute_type=compute_type,
        settings=WhisperSTTService.Settings(
            model=model.value,  # FIX: Extracts the plain string for faster-whisper
            language=Language.EN,
            no_speech_prob=0.4,
        )
    )

    logger.info(
        "WhisperSTTService initialized (Tier 3 local fallback, "
        "model=%s, device=%s, compute_type=%s)",
        model.value, device, compute_type,
    )

    return stt_service