import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask

from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

# FIXED: Imported LLMFullResponseEndFrame to force the buffer to flush
from pipecat.frames.frames import TextFrame, LLMFullResponseEndFrame

from app.tts.sarvam_client import get_sarvam_tts_service

async def main():
    if not os.getenv("SARVAM_API_KEY"):
        print("❌ Error: SARVAM_API_KEY not found in environment.")
        sys.exit(1)

    print("🔊 Starting Sarvam TTS Local Speaker Test...")

    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=False,
            audio_out_enabled=True,
            audio_out_sample_rate=24000, 
        )
    )

    tts_service = get_sarvam_tts_service()
    pipeline = Pipeline([tts_service, transport.output()])
    
    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
    runner = PipelineRunner()

    async def push_text():
        await asyncio.sleep(2) 
        test_phrase = "Namaskaram! Welcome to our restaurant. Ningalkku entha vendathu?"
        print(f"\n💬 Sending text to bulbul:v3: '{test_phrase}'")
        
        # FIXED: Send the text AND tell Pipecat to flush its sentence buffer
        await task.queue_frames([
            TextFrame(test_phrase),
            LLMFullResponseEndFrame()
        ])
        
        # Wait a bit longer to ensure the final audio chunk plays fully
        await asyncio.sleep(10)
        await task.cancel()

    try:
        await asyncio.gather(runner.run(task), push_text())
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
    finally:
        if not task.has_finished():
            await task.cancel()

if __name__ == "__main__":
    os.environ['PYTHONWARNINGS'] = 'ignore'
    asyncio.run(main())