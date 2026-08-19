# test_elevenlabs.py
import asyncio
import uuid
from app.tts.elevenlabs_client import get_primary_tts_service
from pipecat.frames.frames import ErrorFrame, StartFrame

async def main():
    try:
        tts = get_primary_tts_service()
        print(f"✅ Service created: {type(tts).__name__}")
    except Exception as e:
        print(f"❌ Failed to create service: {e}")
        return

    # Send a StartFrame first, like a real pipeline would
    await tts.process_frame(StartFrame(), None)

    try:
        context_id = str(uuid.uuid4())
        real_audio_frames = 0
        async for frame in tts.run_tts(
            "Hello, this is a test of ElevenLabs text to speech.",
            context_id=context_id,
        ):
            print(f"  frame type: {type(frame).__name__}")
            if isinstance(frame, ErrorFrame):
                print(f"  ❌ ERROR DETAIL: {frame.error}")
            else:
                real_audio_frames += 1
        print(f"Real audio frames: {real_audio_frames}")
    except Exception as e:
        print(f"❌ TTS generation raised exception: {e}")

asyncio.run(main())