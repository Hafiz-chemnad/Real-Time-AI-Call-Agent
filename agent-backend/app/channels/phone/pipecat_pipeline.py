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

# STT Providers
from app.stt.sarvam_client import build_sarvam_stt_service
from app.stt.deepgram_client import is_low_confidence, build_deepgram_stt_service
from app.stt.groq_whisper_client import build_groq_stt_service
from app.stt.local_whisper_client import build_local_whisper_stt_service

# TTS Providers
from app.tts.sarvam_client import get_sarvam_tts_service
from app.tts.elevenlabs_client import get_primary_tts_service
from app.tts.cartesia_client import get_fallback_tts_service
from app.tts.kokoro_local import get_local_tts_service
from app.tts.tts_with_fallback import run_with_tts_fallback
from app.tts.phrase_cache import PhraseCache


# ---------------------------------------------------------------------------
# 0. Start Gate Processor
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 0. Start Gate Processor
# ---------------------------------------------------------------------------
class StartGateProcessor(FrameProcessor):
    def __init__(self, is_resume: bool = False):
        super().__init__()
        self.started = is_resume
        self._has_injected_resume_start = False

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        # THE FIX: If resuming, hijack the very first incoming Twilio audio frame 
        # to fire a StartFrame downstream, waking up the frozen pipeline.
        if self.started and not self._has_injected_resume_start and not isinstance(frame, StartFrame):
            self._has_injected_resume_start = True
            await self.push_frame(StartFrame(), direction)

        if isinstance(frame, StartFrame):
            self.started = True
            self._has_injected_resume_start = True 
            await self.push_frame(frame, direction)
            return

        if not self.started:
            return  

        await self.push_frame(frame, direction)


# ---------------------------------------------------------------------------
# 1. Custom Brain Processor
# ---------------------------------------------------------------------------
class Milestone1BrainProcessor(FrameProcessor):
    def __init__(
        self,
        business_id: str,
        call_sid: str,
        account_sid: str,
        auth_token: str,
        current_language: str,
        session_state: dict = None,
        is_resume: bool = False,
        resume_text: str = None,
        transcript_lines_acc: list = None,
        tools_called_acc: list = None
    ):
        super().__init__()
        self.business_id = business_id
        self.call_sid = call_sid
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.current_language = current_language
        self.session_state = session_state or {}
        self.phrase_cache = PhraseCache()
        self._current_turn_task: asyncio.Task | None = None
        self._turn_lock = asyncio.Lock()

        # Rebuild-aware state
        self.is_resume = is_resume
        self.resume_text = resume_text
        self._resume_triggered = False

        # Signals to the outer loop why the pipeline stopped
        self.pending_language_switch: tuple[str, str] | None = None

        # Accumulators persist across pipeline rebuilds
        self._transcript_lines = transcript_lines_acc if transcript_lines_acc is not None else []
        self._tools_called = tools_called_acc if tools_called_acc is not None else []
        self._escalated = False
        self._escalation_reason: str | None = None
        self._log_saved = False

        # Set externally via on_task_created (see run_with_tts_fallback)
        # once the real PipelineTask exists — task.cancel() is the only
        # confirmed-working way to actually stop the pipeline and trigger
        # a rebuild; pushing a bare CancelFrame was tested and hangs.
        self.task_ref = None

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        if self.is_resume and not self._resume_triggered:
            self._resume_triggered = True
            if self.resume_text:
                self._current_turn_task = asyncio.create_task(self._speak(self.resume_text, direction))

        if isinstance(frame, StartFrame):
            await self.push_frame(frame, direction)
            if not self.is_resume:
                asyncio.create_task(self._speak_greeting(direction))
            return

        if isinstance(frame, UserStartedSpeakingFrame):
            if self._current_turn_task and not self._current_turn_task.done():
                self._current_turn_task.cancel()
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, TranscriptionFrame):
            if getattr(frame, "is_final", True) is False:
                return

            transcript = getattr(frame, "text", "")
            if isinstance(transcript, list):
                transcript = " ".join(transcript)

            if not transcript or not transcript.strip():
                return

            confidence = getattr(frame, "confidence", None)
            if confidence is not None and is_low_confidence(confidence):
                await self._speak("Sorry, I didn't quite catch that — could you say that again?", direction)
                return

            if self._current_turn_task and not self._current_turn_task.done():
                self._current_turn_task.cancel()

            self._current_turn_task = asyncio.create_task(
                self._handle_turn(transcript, direction)
            )
            return

        await self.push_frame(frame, direction)

    async def _handle_turn(self, transcript: str, direction):
        try:
            async with self._turn_lock:
                result = await process_turn(transcript, self.session_state, business_id=self.business_id)
                self.session_state = result.get("session_state", {})

                # 1. Explicit language-switch request from the LLM
                if result.get("language_switch_requested"):
                    new_lang = result["language_switch_requested"]
                    ack_text = result["response"]

                    self._transcript_lines.append(f"Caller: {transcript}")
                    self._transcript_lines.append(f"AI: {ack_text}")

                    # DISABLED: Transport cannot survive pipeline cancellation
                    # self.pending_language_switch = (new_lang, ack_text)
                    # if self.task_ref:
                    #     await self.task_ref.cancel()
                    # return

                # 2. Turn-1 silent lock disagreeing with the Sarvam-first default
                if not self.is_resume and self.current_language == "ml" and self.session_state.get("call_language") == "en":
                    ack_text = result["response"]

                    self._transcript_lines.append(f"Caller: {transcript}")
                    self._transcript_lines.append(f"AI: {ack_text}")

                    # DISABLED: Transport cannot survive pipeline cancellation
                    # self.pending_language_switch = ("en", ack_text)
                    # if self.task_ref:
                    #     await self.task_ref.cancel()
                    # return

                response_text = result["response"]

            await self._speak(response_text, direction)

            self._transcript_lines.append(f"Caller: {transcript}")
            self._transcript_lines.append(f"AI: {response_text}")
            if result.get("tool_called"):
                self._tools_called.append(result["tool_called"])
            if result.get("escalation"):
                self._escalated = True
                self._escalation_reason = result["escalation"]

            if result.get("escalation") in ("human_request", "frustration"):
                await trigger_emergency_transfer(self.call_sid, self.account_sid, self.auth_token, self.business_id)

        except asyncio.CancelledError:
            raise

    async def _speak_greeting(self, direction):
        greeting = "Hi, thanks for calling! How can I help you today?"
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Business).where(Business.id == uuid.UUID(self.business_id)))
                biz = result.scalar_one_or_none()
                if biz and getattr(biz, "greeting_text", None):
                    greeting = biz.greeting_text
        except Exception:
            pass
        await self._speak(greeting, direction)

    async def _speak(self, text: str, direction):
        await self.push_frame(LLMFullResponseStartFrame(), direction)
        await self.push_frame(TextFrame(text=text), direction)
        await self.push_frame(LLMFullResponseEndFrame(), direction)

    async def save_call_log(self):
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
                    tools_called=self._tools_called or None,
                    escalated=self._escalated,
                    escalation_reason=self._escalation_reason,
                )
                session.add(log)
                await session.commit()
        except Exception as e:
            print(f"Failed to save call log for call_sid={self.call_sid}: {e}")


# ---------------------------------------------------------------------------
# 2. Fatal Fallback
# ---------------------------------------------------------------------------
async def trigger_emergency_transfer(call_sid: str, account_sid: str, auth_token: str, business_id: str):
    transfer_number = "+1234567890"
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Business).where(Business.id == uuid.UUID(business_id)))
            business = result.scalar_one_or_none()
            if business and business.transfer_numbers and "emergency" in business.transfer_numbers:
                transfer_number = business.transfer_numbers["emergency"]
    except Exception:
        pass

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
    transfer_twiml = (
        f"<Response><Say>I'm having a brief technical connection issue, let me "
        f"transfer you right now.</Say><Dial>{transfer_number}</Dial></Response>"
    )
    async with aiohttp.ClientSession() as session:
        await session.post(url, auth=aiohttp.BasicAuth(account_sid, auth_token), data={"Twiml": transfer_twiml})


# ---------------------------------------------------------------------------
# 3. Main Pipeline Builder
# ---------------------------------------------------------------------------
async def run_pipecat_pipeline(transport, call_sid: str, account_sid: str, auth_token: str, business_id: str):

    current_language = "ml"
    resume_text = None
    session_state = {}
    transcript_lines_acc = []
    tools_called_acc = []

    final_brain = None

    try:
        while True:
            stt_service_getters = [
                build_sarvam_stt_service,
                build_deepgram_stt_service,
                build_groq_stt_service,
                build_local_whisper_stt_service,
            ]

            if current_language == "ml":
                tts_service_getters = [
                    get_sarvam_tts_service,
                    get_local_tts_service,
                ]
            else:
                tts_service_getters = [
                    get_primary_tts_service,
                    get_fallback_tts_service,
                    get_local_tts_service,
                ]

            pipeline_success = False

            for i, get_stt_service in enumerate(stt_service_getters):
                try:
                    stt_service = get_stt_service()
                except Exception:
                    continue

                start_gate = StartGateProcessor(is_resume=(resume_text is not None))
                brain = Milestone1BrainProcessor(
                    business_id=business_id,
                    call_sid=call_sid,
                    account_sid=account_sid,
                    auth_token=auth_token,
                    current_language=current_language,
                    session_state=session_state,
                    is_resume=(resume_text is not None),
                    resume_text=resume_text,
                    transcript_lines_acc=transcript_lines_acc,
                    tools_called_acc=tools_called_acc
                )
                final_brain = brain

                try:
                    
                    await run_with_tts_fallback(
                        tts_service_getters=tts_service_getters,
                        upstream_processors=[transport.input(), start_gate, stt_service, brain],
                        downstream_processors=[transport.output()],
                        on_task_created=lambda task: setattr(brain, "task_ref", task),
                        is_resume=(resume_text is not None)  # 👈 THIS IS THE MISSING LINE
                    )

                    if brain.pending_language_switch:
                        new_lang, ack_text = brain.pending_language_switch
                        current_language = new_lang
                        resume_text = ack_text

                        session_state = brain.session_state
                        transcript_lines_acc = brain._transcript_lines
                        tools_called_acc = brain._tools_called

                        pipeline_success = "REBUILD"
                        break

                    pipeline_success = True
                    break

                except Exception:
                    continue

            if pipeline_success == "REBUILD":
                continue
            elif pipeline_success:
                break
            else:
                await trigger_emergency_transfer(call_sid, account_sid, auth_token, business_id)
                break
    finally:
        if final_brain is not None:
            await final_brain.save_call_log()