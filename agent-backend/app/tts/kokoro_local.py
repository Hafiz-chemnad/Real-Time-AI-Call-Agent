# app/tts/kokoro_local.py
import os

try:
    from pipecat.services.kokoro import KokoroTTSService
    _KOKORO_AVAILABLE = True
except ImportError:
    KokoroTTSService = None
    _KOKORO_AVAILABLE = False


def get_local_tts_service():
    """
    Initializes the Tier 3 Kokoro-82M Local TTS Service.
    Runs entirely offline on the CPU (Apache 2.0 License).
    Deferred: requires Python 3.11+ (pipecat-ai[kokoro] dependency constraint).
    """
    if not _KOKORO_AVAILABLE:
        print("Warning: Kokoro not installed (requires Python 3.11+). Tier 3 fallback disabled.")
        return None

    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, "models", "model.onnx")
    voices_path = os.path.join(base_dir, "models", "af_bella.bin")

    if not os.path.exists(model_path) or not os.path.exists(voices_path):
        print("Warning: Kokoro ONNX model/voices not found. Tier 3 fallback disabled.")
        return None

    tts_service = KokoroTTSService(
        model_path=model_path,
        voices_path=voices_path,
        voice="af_bella",
        sample_rate=8000
    )

    return tts_service