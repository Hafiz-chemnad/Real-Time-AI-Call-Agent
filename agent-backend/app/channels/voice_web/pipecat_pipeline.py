from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

from app.tts.elevenlabs_client import get_primary_tts_service
from app.tts.cartesia_client import get_fallback_tts_service
from app.tts.kokoro_local import get_local_tts_service
from app.tts.tts_with_fallback import run_with_tts_fallback
from app.stt.deepgram_client import build_deepgram_stt_service
from app.stt.groq_whisper_client import build_groq_stt_service
from app.stt.local_whisper_client import build_local_whisper_stt_service

from app.channels.phone.pipecat_pipeline import Milestone1BrainProcessor


async def run_webrtc_pipeline(transport):
    """Builds and runs the Pipecat loop specifically for the web widget."""

    vad_analyzer = SileroVADAnalyzer(params=VADParams(
        min_speech_duration=0.25
    ))

    stt_service_getters = [
        build_groq_stt_service,
        build_deepgram_stt_service,
        build_local_whisper_stt_service,
    ]

    last_error = None
    for i, get_stt_service in enumerate(stt_service_getters):
        try:
            stt_service = get_stt_service()
        except Exception as exc:
            last_error = exc
            print(f"STT tier {i} failed to initialize: {exc}, trying next tier...")
            continue

        brain = Milestone1BrainProcessor()

        try:
            print(f"WebRTC Pipeline starting (STT tier {i}: {type(stt_service).__name__})...")

            await run_with_tts_fallback(
                tts_service_getters=[
                    get_fallback_tts_service,
                    get_primary_tts_service,
                    get_local_tts_service,
                ],
                upstream_processors=[
                    transport.input(),
                    stt_service,
                    brain,
                ],
                downstream_processors=[
                    transport.output(),
                ],
            )
            return

        except Exception as exc:
            last_error = exc
            print(f"WebRTC pipeline with STT tier {i} failed: {exc}, trying next STT tier...")
            continue

    print(f"WebRTC pipeline exception: all STT tiers failed. Last error: {last_error}")