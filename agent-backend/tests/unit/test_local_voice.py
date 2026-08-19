import asyncio
import os
import logging
from dotenv import load_dotenv

# Pipecat dependencies
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import TranscriptionFrame, TextFrame
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams  # <-- NEW IMPORT

# Import your STT/TTS getters based on the files you provided
from app.stt.groq_whisper_client import build_groq_stt_service
from app.tts.cartesia_client import get_fallback_tts_service 

# Import your fixed Orchestrator
from app.brain.orchestrator import process_turn

load_dotenv(override=True)
logging.basicConfig(level=logging.WARNING)

class OrchestratorProcessor(FrameProcessor):
    """
    Custom Pipecat node that intercepts STT text, runs your orchestrator, 
    and yields the AI's text response to the TTS engine.
    """
    def __init__(self):
        super().__init__()
        # Use Smile Dental test ID
        self.business_id = "11111111-1111-1111-1111-111111111111"
        self.session_state = {
            "chat_history": [],
            "pending_tool_call": None
        }

    async def process_frame(self, frame, direction=FrameDirection.DOWNSTREAM):
        # 1. CRITICAL FIX: Let Pipecat handle internal state (StartFrame, EndFrame)
        await super().process_frame(frame, direction)

        # 2. Catch user speech transcriptions from Groq
        if isinstance(frame, TranscriptionFrame):
            transcript = frame.text.strip()
            
            # Only process if Groq actually heard words
            if transcript:
                print(f"\n👤 YOU: \"{transcript}\"")

                # Call your brain
                result = await process_turn(
                    transcript=transcript,
                    session_state=self.session_state,
                    business_id=self.business_id
                )

                # Update memory for the next turn
                self.session_state = result.get("session_state", {})
                response_text = result.get("response", "")
                
                print(f"🤖 AI: \"{response_text}\"")

                # Push the AI's text response to Cartesia TTS
                await self.push_frame(TextFrame(response_text))
        
        # 3. Pass all original frames (audio bytes, start frames, etc) downstream
        await self.push_frame(frame, direction)

async def main():
    # 1. Setup local Microphone and Speaker transport
    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=16000,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.8)), # <-- INCREASED STOP_SECS
        )
    )

    # 2. Initialize Services (Groq Primary STT & Cartesia TTS)
    try:
        stt_service = build_groq_stt_service()
        tts_service = get_fallback_tts_service() 
    except Exception as e:
        print(f"❌ Failed to load services: {e}")
        return

    if not tts_service:
        print("❌ Cartesia API Key missing. Exiting.")
        return

    # 3. Initialize Custom Orchestrator Node
    orchestrator_node = OrchestratorProcessor()

    # 4. Build the continuous audio pipeline
    # Pipeline Flow: Mic -> VAD -> STT (Groq) -> Orchestrator -> TTS (Cartesia) -> Speaker
    pipeline = Pipeline([
        transport.input(),
        stt_service,
        orchestrator_node,
        tts_service,
        transport.output()
    ])

    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
    runner = PipelineRunner()

    print("\n" + "="*60)
    print("🎙️ LOCAL VOICE TEST STARTED")
    print("⚠️  RULE: You MUST be wearing headphones for this test!")
    print("="*60 + "\n")
    
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())