import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.audio.vad.silero import SileroVADAnalyzer

from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.frames.frames import Frame, TranscriptionFrame, InterimTranscriptionFrame

from app.stt.sarvam_client import build_sarvam_stt_service

class TranscriptPrinter(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, TranscriptionFrame):
            print(f"✅ Final: {frame.text}")
        elif isinstance(frame, InterimTranscriptionFrame):
            print(f"⏳ {frame.text}")

async def main():
    if not os.getenv("SARVAM_API_KEY"):
        print("❌ Error: SARVAM_API_KEY not found in environment.")
        sys.exit(1)

    print("🎙️ Starting Sarvam STT Local Mic Test...")
    print("Speak in English, Malayalam, or a mix of both. Press Ctrl+C to stop.")

    # Reverted to the simpler VAD setup (we just removed vad_enabled=True)
    transport = LocalAudioTransport(
    LocalAudioTransportParams(
        audio_in_enabled=True,
        audio_out_enabled=False,
        audio_in_sample_rate=8000,   # match build_sarvam_stt_service()'s sample_rate=8000
        vad_analyzer=SileroVADAnalyzer(),
     )
    )
    
    stt_service = build_sarvam_stt_service()
    printer = TranscriptPrinter()

    pipeline = Pipeline([transport.input(), stt_service, printer])

    # The actual crash fix: 'params=' is strictly required
    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
    runner = PipelineRunner()

    try:
        await runner.run(task)
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
    finally:
        await task.cancel()

if __name__ == "__main__":
    os.environ['PYTHONWARNINGS'] = 'ignore'
    asyncio.run(main())