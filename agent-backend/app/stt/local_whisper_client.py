"""
app/stt/local_whisper_client.py

Tier 3 (Local Offline Fallback) STT client — faster-whisper running
locally via Pipecat's native WhisperSTTService, no internet dependency
at inference time (model weights are downloaded once from HuggingFace
Hub on first use, then cached).

Owned by: Person 1 (STT Engineer, Track 1 - "The Ears")

Activates only if BOTH Deepgram (Tier 1) and Groq (Tier 2) are
unreachable — e.g. total internet outage. Last line of defense to keep
a call from dropping entirely.

Note: unlike DeepgramSTTService/GroqSTTService (which stream audio
continuously to a remote websocket), WhisperSTTService is a
SegmentedSTTService — Pipecat buffers audio between VAD-detected speech
boundaries internally and runs Whisper once per segment. This is a
Pipecat-level implementation detail, not something this client needs to
manage manually.
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
    """
    Builds a WhisperSTTService running a local faster-whisper model.

    Why these defaults:
      - model=Model.DISTIL_MEDIUM_EN: Pipecat's own default, and the
        ONLY English-only model in the enum (all others — TINY, BASE,
        SMALL, MEDIUM, LARGE, LARGE_V3_TURBO, DISTIL_LARGE_V2 — are
        multilingual). English-only models are faster and slightly
        more accurate for English-only use cases like this project.
        (Earlier draft incorrectly referenced "Model.BASE_EN", which
        does not exist in Pipecat's enum — there is no "_EN" suffix
        variant of BASE/TINY/etc; only DISTIL_MEDIUM_EN is English-only.)
        If CPU inference proves too slow in practice, Model.TINY is the
        smallest/fastest multilingual option to fall back to.
      - device="cpu": assumes no GPU is guaranteed to be available on
        the dev/prod box. Change to "cuda" only after confirming a GPU
        is actually present, otherwise this will error at load time.
      - compute_type="int8": quantized inference, meaningfully faster
        on CPU with a small, acceptable accuracy tradeoff for a rarely
        -used fallback path.

    Why no api_key/env var check here (unlike Deepgram/Groq): this tier
    doesn't call a remote API, so there's no credential to validate.
    The only external dependency is the one-time HuggingFace model
    download on first use — set HF_TOKEN in .env (already done in
    Step 1) to avoid rate-limiting during that download.

    Returns:
        A configured WhisperSTTService instance, not yet linked into
        a Pipeline. The underlying faster-whisper model is lazy-loaded
        by Pipecat itself on first use, not at construction time.
    """
    stt_service = WhisperSTTService(
        model=model,
        device=device,
        compute_type=compute_type,
        language=Language.EN,
        no_speech_prob=0.4,  # filters out segments Whisper thinks are
                             # silence/non-speech; default Pipecat value
    )

    logger.info(
        "WhisperSTTService initialized (Tier 3 local fallback, "
        "model=%s, device=%s, compute_type=%s)",
        model, device, compute_type,
    )

    return stt_service