import asyncio
import aiohttp
from pipecat.processors.frame_processor import FrameProcessor
import uuid
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.business import Business
from app.models.call_log import CallLog
from pipecat.frames.frames import (
    StartFrame,
    TranscriptionFrame,
    TextFrame,
    UserStartedSpeakingFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
)

from app.brain.orchestrator import process_turn
from app.tts.elevenlabs_client import get_primary_tts_service
from app.tts.cartesia_client import get_fallback_tts_service
from app.tts.kokoro_local import get_local_tts_service
from app.tts.tts_with_fallback import run_with_tts_fallback
from app.tts.phrase_cache import PhraseCache
from app.stt.deepgram_client import is_low_confidence, build_deepgram_stt_service
from app.stt.groq_whisper_client import build_groq_stt_service
from app.stt.local_whisper_client import build_local_whisper_stt_service


# ---------------------------------------------------------------------------
# 0. Start Gate Processor (Buffers early audio frames until StartFrame arrives)
# ---------------------------------------------------------------------------
class StartGateProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.started = False

    async def process_frame(self, frame, direction):
        # CRITICAL: Always call super first for Pipecat internal bookkeeping
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            self.started = True
            await self.push_frame(frame, direction)
            return

        if not self.started:
            return  # Drop audio frames arriving before StartFrame

        await self.push_frame(frame, direction)


# ---------------------------------------------------------------------------
# 1. Custom Brain Processor (Bridging STT -> Single-Pass Brain -> TTS)
# ---------------------------------------------------------------------------
class Milestone1BrainProcessor(FrameProcessor):
    def __init__(self, business_id: str, call_sid: str, account_sid: str, auth_token: str):
        super().__init__()
        self.business_id = business_id
        self.call_sid = call_sid
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.session_state = {}
        self.phrase_cache = PhraseCache()
        self._current_turn_task: asyncio.Task | None = None
        self._turn_lock = asyncio.Lock()

        # Call-level accumulators for the single CallLog row written at hangup
        self._transcript_lines: list[str] = []
        self._tools_called: list[dict] = []
        self._escalated = False
        self._escalation_reason: str | None = None
        self._log_saved = False

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            await self.push_frame(frame, direction)
            await self._speak(
                "Hi, thanks for calling! How can I help you today?",
                direction,
            )
            return

        if isinstance(frame, UserStartedSpeakingFrame):
            # Real barge-in: if a turn is currently being generated/spoken,
            # cancel it immediately so the new utterance takes over cleanly.
            if self._current_turn_task and not self._current_turn_task.done():
                print("User interrupted mid-response — cancelling in-flight turn.")
                self._current_turn_task.cancel()
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, TranscriptionFrame):

            # Ignore partial transcripts, wait for the full sentence
            if getattr(frame, "is_final", True) is False:
                return

            transcript = getattr(frame, "text", "")
            if isinstance(transcript, list):
                transcript = " ".join(transcript)

            if not transcript or not transcript.strip():
                return

            print(f"Received transcription: '{transcript}'")

            confidence = getattr(frame, "confidence", None)
            if confidence is not None and is_low_confidence(confidence):
                print(f"Low-confidence transcript ({confidence:.2f}): '{transcript}' — asking caller to repeat")
                await self._speak(
                    "Sorry, I didn't quite catch that — could you say that again?",
                    direction,
                )
                return

            # If a previous turn is still in flight (shouldn't normally happen
            # since UserStartedSpeakingFrame cancels it first, but this closes
            # the race if two transcriptions land back-to-back), cancel it now.
            if self._current_turn_task and not self._current_turn_task.done():
                self._current_turn_task.cancel()

            self._current_turn_task = asyncio.create_task(
                self._handle_turn(transcript, direction)
            )
            return

        await self.push_frame(frame, direction)

    async def _handle_turn(self, transcript: str, direction):
        """Runs one full turn (LLM + push to TTS), cancellable mid-flight."""
        try:
            async with self._turn_lock:
                result = await process_turn(transcript, self.session_state, business_id=self.business_id)
                response_text = result["response"]
                self.session_state = result.get("session_state", {})

            print(f"🧠 LLM decided to say: '{response_text}'")
            await self._speak(response_text, direction)

            # Accumulate this turn into the call-level record
            self._transcript_lines.append(f"Caller: {transcript}")
            self._transcript_lines.append(f"AI: {response_text}")
            if result.get("tool_called"):
                self._tools_called.append(result["tool_called"])
            if result.get("escalation"):
                self._escalated = True
                self._escalation_reason = result["escalation"]

            # Genuine caller-requested escalation (not a crash) — actually
            # transfer the call after the AI's verbal acknowledgement finishes.
            if result.get("escalation") in ("human_request", "frustration"):
                print(f"Escalation detected ({result['escalation']}) — transferring call {self.call_sid}")
                await trigger_emergency_transfer(
                    self.call_sid, self.account_sid, self.auth_token, self.business_id
                )

        except asyncio.CancelledError:
            print(f"Turn for '{transcript}' was cancelled (interrupted).")
            raise  # required — swallowing this breaks asyncio's cancellation contract

    async def _speak(self, text: str, direction):
        """Pushes one turn's text as a properly bounded unit, so TTS
        (Cartesia) flushes cleanly and never concatenates with the next turn."""
        await self.push_frame(LLMFullResponseStartFrame(), direction)
        await self.push_frame(TextFrame(text=text), direction)
        await self.push_frame(LLMFullResponseEndFrame(), direction)

    async def save_call_log(self):
        """Writes exactly one CallLog row for this call, at hangup. Safe to
        call multiple times — only the first call actually writes."""
        if self._log_saved:
            return
        self._log_saved = True

        if not self._transcript_lines:
            return

        try:
            from app.core.pii_redaction import redact_pii

            redacted_transcript = redact_pii("\n".join(self._transcript_lines))

            async with AsyncSessionLocal() as session:
                log = CallLog(
                    business_id=uuid.UUID(self.business_id),
                    channel="phone",
                    transcript=redacted_transcript,
                    summary=None,
                    tools_called=self._tools_called or None,
                    latency_metrics=None,
                    escalated=self._escalated,
                    escalation_reason=self._escalation_reason,
                )
                session.add(log)
                await session.commit()
                print(f"Call log saved for call_sid={self.call_sid}")
        except Exception as e:
            print(f"Failed to save call log for call_sid={self.call_sid}: {e}")


# ---------------------------------------------------------------------------
# 2. Fatal Fallback: Transfer call on crash
# ---------------------------------------------------------------------------
async def trigger_emergency_transfer(call_sid: str, account_sid: str, auth_token: str, business_id: str):
    transfer_number = "+1234567890"  # Default fallback

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Business).where(Business.id == uuid.UUID(business_id)))
            business = result.scalar_one_or_none()
            if business and business.transfer_numbers and "emergency" in business.transfer_numbers:
                transfer_number = business.transfer_numbers["emergency"]
    except Exception as e:
        print(f"Failed to fetch real transfer number, using fallback. Error: {e}")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
    transfer_twiml = (
        f"<Response><Say>I'm having a brief technical connection issue, let me "
        f"transfer you right now.</Say><Dial>{transfer_number}</Dial></Response>"
    )
    async with aiohttp.ClientSession() as session:
        await session.post(
            url,
            auth=aiohttp.BasicAuth(account_sid, auth_token),
            data={"Twiml": transfer_twiml}
        )
        print(f"Emergency transfer triggered for Call SID: {call_sid} to {transfer_number}")


# ---------------------------------------------------------------------------
# 3. Main Pipeline Builder
# ---------------------------------------------------------------------------
async def run_pipecat_pipeline(transport, call_sid: str, account_sid: str, auth_token: str, business_id: str):
    stt_service_getters = [
        build_deepgram_stt_service,      # Primary: Deepgram Nova, streaming, telephony-tuned
        build_groq_stt_service,          # Fallback Tier 1
        build_local_whisper_stt_service, # Fallback Tier 2
    ]

    last_error = None
    brain = None
    try:
        for i, get_stt_service in enumerate(stt_service_getters):
            try:
                stt_service = get_stt_service()
            except Exception as exc:
                last_error = exc
                print(f"STT tier {i} failed to initialize: {exc}, trying next tier...")
                continue

            start_gate = StartGateProcessor()
            brain = Milestone1BrainProcessor(
                business_id=business_id,
                call_sid=call_sid,
                account_sid=account_sid,
                auth_token=auth_token,
            )

            try:
                print(f"Pipeline starting (STT tier {i}: {type(stt_service).__name__})...")

                await run_with_tts_fallback(
                    tts_service_getters=[
                        get_primary_tts_service,    # ElevenLabs first (River voice, confirmed working)
                        get_fallback_tts_service,   # Cartesia fallback
                        get_local_tts_service,
                    ],
                    upstream_processors=[
                        transport.input(),
                        start_gate,
                        stt_service,
                        brain,
                    ],
                    downstream_processors=[
                        transport.output(),
                    ],
                )
                return  # success — finally block below still saves the log

            except Exception as exc:
                last_error = exc
                print(f"Pipeline with STT tier {i} failed: {exc}, trying next STT tier...")
                continue

        # Every STT tier failed
        print(f"Fatal pipeline exception: all STT tiers failed.")
        await trigger_emergency_transfer(call_sid, account_sid, auth_token, business_id)
    finally:
        # Fires exactly once, on every possible exit path — success,
        # STT-tier exhaustion, or any unexpected exception — using
        # whichever brain instance was actually accumulating the
        # conversation. save_call_log() is idempotent, so this is safe
        # even if the success path above already called it via return.
        if brain is not None:
            await brain.save_call_log()