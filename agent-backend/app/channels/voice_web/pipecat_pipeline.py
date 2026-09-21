# app/channels/voice_web/pipecat_pipeline.py
from app.tts.sarvam_client import get_sarvam_tts_service
from app.tts.elevenlabs_client import get_primary_tts_service
from app.tts.cartesia_client import get_fallback_tts_service
from app.tts.kokoro_local import get_local_tts_service
from app.tts.tts_with_fallback import run_with_tts_fallback

from app.stt.sarvam_client import build_sarvam_stt_service
from app.stt.deepgram_client import build_deepgram_stt_service
from app.stt.groq_whisper_client import build_groq_stt_service
from app.stt.local_whisper_client import build_local_whisper_stt_service

from app.channels.phone.pipecat_pipeline import Milestone1BrainProcessor


async def run_webrtc_pipeline(transport, business_id: str):
    """
    Builds and runs the Pipecat loop for the dashboard's browser mic test
    widget — mirrors app/channels/phone/pipecat_pipeline.py's structure
    (Sarvam-first STT/TTS, business_id threading, language-switch rebuild
    via task.cancel(), call-log persistence) minus anything Twilio-specific
    (no call_sid/account_sid/auth_token, no emergency transfer — there's no
    real phone call to transfer here, just a browser test session).
    """

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
                except Exception as exc:
                    print(f"STT tier {i} failed to initialize: {exc}, trying next tier...")
                    continue

                brain = Milestone1BrainProcessor(
                    business_id=business_id,
                    call_sid="webrtc-test-session",  # no real Twilio call — used only as a save_call_log() identifier
                    account_sid="",
                    auth_token="",
                    current_language=current_language,
                    session_state=session_state,
                    is_resume=(resume_text is not None),
                    resume_text=resume_text,
                    transcript_lines_acc=transcript_lines_acc,
                    tools_called_acc=tools_called_acc,
                )
                final_brain = brain

                try:
                    print(f"WebRTC Pipeline starting (Lang: {current_language}, STT tier {i}: {type(stt_service).__name__})...")

                    await run_with_tts_fallback(
                        tts_service_getters=tts_service_getters,
                        upstream_processors=[transport.input(), stt_service, brain],
                        downstream_processors=[transport.output()],
                        on_task_created=lambda task: setattr(brain, "task_ref", task),
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

                except Exception as exc:
                    print(f"WebRTC pipeline with STT tier {i} failed: {exc}, trying next STT tier...")
                    continue

            if pipeline_success == "REBUILD":
                continue
            elif pipeline_success:
                break
            else:
                print("WebRTC pipeline exception: all STT tiers failed.")
                break
    finally:
        if final_brain is not None:
            await final_brain.save_call_log()