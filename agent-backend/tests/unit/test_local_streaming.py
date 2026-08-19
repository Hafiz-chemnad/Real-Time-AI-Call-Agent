import asyncio
import os
import sys
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Pipecat Local Transport & VAD
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.local.audio import LocalAudioTransport
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

# Pipeline Setup
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner

# STT, LLM, and TTS Services
from app.stt.groq_whisper_client import build_groq_stt_service
from app.tts.cartesia_client import get_fallback_tts_service

# Native Pipecat LLM Service
from pipecat.services.openai import OpenAILLMService
from pipecat.messages.messages import OpenAIMessage

# ---------------------------------------------------------
# 1. Parameter Patch for Desktop Audio & Tuned VAD
# ---------------------------------------------------------
class PatchedTransportParams(TransportParams):
    input_device_index: int | None = None
    output_device_index: int | None = None
    audio_in_sample_rate: int = 16000
    audio_out_sample_rate: int = 16000

# ---------------------------------------------------------
# 2. Main Native Streaming E2E Execution
# ---------------------------------------------------------
async def run_local_streaming_test():
    print("\n" + "="*60)
    print("⚡ LIVE NATIVE STREAMING TEST (Groq STT -> Streaming LLM -> Cartesia)")
    print("="*60)

    # TUNED VAD: stop_secs=0.8 gives you time to pause/breathe without cutting you off
    vad_analyzer = SileroVADAnalyzer(
        params=VADParams(
            min_speech_duration=0.25,
            start_secs=0.2,
            stop_secs=0.8,  
            confidence=0.7
        )
    )

    transport = LocalAudioTransport(
        params=PatchedTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=vad_analyzer
        )
    )

    print("👂 Initializing Groq Whisper STT...")
    stt = build_groq_stt_service()

    print("🧠 Initializing Streaming LLM...")
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini", # Lightning-fast time-to-first-token
    )

    initial_context = llm.create_context(
        [
            OpenAIMessage(
                role="system",
                content="You are a helpful and polite voice assistant for Smile Dental. Keep your answers concise, conversational, and natural for phone calls."
            )
        ]
    )
    context_aggregator = llm.create_context_aggregator(initial_context)

    print("🗣️ Initializing Cartesia TTS (Streaming)...")
    tts = get_fallback_tts_service()

    # Build the native Pipecat streaming pipeline
    pipeline = Pipeline([
        transport.input(),
        stt,
        context_aggregator.user(),
        llm,
        tts,
        transport.output(),
        context_aggregator.assistant(),
    ])

    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    print("\n✅ STREAMING PIPELINE READY! Speak naturally into your microphone.")
    print("Notice how it responds instantly without cutting you off prematurely.")
    print("Press Ctrl+C to end the test.\n")

    try:
        await runner.run(task)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("\nTest finished successfully.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_local_streaming_test())