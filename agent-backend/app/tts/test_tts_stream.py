# app/tts/test_tts_stream.py
import asyncio
import wave
import os
import sys

from loguru import logger
logger.remove()
logger.add(sys.stderr, level="TRACE")

from pipecat.frames.frames import (
    TextFrame, 
    AudioRawFrame, 
    EndFrame,
    LLMFullResponseEndFrame,
    TTSStoppedFrame
)
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask

from app.tts.elevenlabs_client import get_primary_tts_service


class AudioSaverProcessor(FrameProcessor):
    def __init__(self, filename="tts_test_output.wav"):
        super().__init__()
        self.filename = filename
        self.audio_data = bytearray()
        self.first_chunk_received = False

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, AudioRawFrame):
            if not self.first_chunk_received:
                print("\n" + "="*50)
                print("SUCCESS: First raw audio buffer received from ElevenLabs TTS!")
                print("="*50 + "\n")
                self.first_chunk_received = True
            
            self.audio_data.extend(frame.audio)
            await self.push_frame(frame, direction)

        elif isinstance(frame, TTSStoppedFrame):
            print("\nStream complete. Saving audio file...")
            self._save_to_wav()
            await self.push_frame(frame, direction)
            await self.push_frame(EndFrame())
            
        else:
            await self.push_frame(frame, direction)

    def _save_to_wav(self):
        with wave.open(self.filename, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            # CHANGED: Save the file as 16kHz to match ElevenLabs output
            wav_file.setframerate(16000) 
            wav_file.writeframes(self.audio_data)
        print(f"Audio saved successfully to: {os.path.abspath(self.filename)}\n")


async def main():
    tts_service = get_primary_tts_service()
    audio_saver = AudioSaverProcessor()

    pipeline = Pipeline([
        tts_service,
        audio_saver
    ])

    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    async def simulate_stream():
        await asyncio.sleep(2)
        
        tokens = [
            "Hello,", " thank you", " for calling", " Tony's", " Pizza.", 
            " How", " can I", " help you", " today?"
        ]

        print("\nMock LLM: Starting generation...")
        for token in tokens:
            print(f"Mock LLM: Queueing '{token}'")
            await task.queue_frame(TextFrame(text=token))
            await asyncio.sleep(0.05) 

        print("Mock LLM: Finished generating. Sending End Frame...")
        await task.queue_frame(LLMFullResponseEndFrame())

    asyncio.create_task(simulate_stream())

    print("Starting Standalone TTS Validation...")
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
    
    # FORCE EXIT: Kills the background ElevenLabs keep-alive threads so the script stops hanging
    sys.exit(0)