# app/brain/orchestrator.py

from typing import Optional

from app.brain.gateway import call_llm
from app.brain.router import get_model_for_task
from app.brain.intent_classifier import classify_intent
from app.brain.response_generator import generate_response
from app.brain.tool_decision import decide_tool_call, decide_correction
from app.brain.guardrails.escalation import check_escalation, get_escalation_response
from app.brain.guardrails.prompt_guardrails import validate_prompt
from app.brain.guardrails.confirmation import (
    create_booking_confirmation,
    classify_confirmation_reply,
)
from app.knowledge.selector import get_context
from app.tools.execution.executor import execute_tool
from app.observability.langfuse_tracer import trace_turn

SYSTEM_PROMPT = (
    "You are a friendly, professional receptionist answering calls for a business. "
    "Keep responses short and conversational, like a real front-desk person would speak "
    "on the phone — not an essay. Usually 1-2 sentences. No headers, no bullet points, "
    "no markdown formatting. Just talk naturally."
)

# Hardcoded sample knowledge for Milestone 1 testing — Milestone 3 replaces
# this with per-business content loaded from Postgres.
SAMPLE_KNOWLEDGE = [
    "Business hours: Monday-Friday 9am-6pm, Saturday 10am-2pm, closed Sundays.",
    "We accept Delta Dental and Cigna insurance.",
    "Cancellations require 24 hours notice.",
]


async def process_turn(transcript: str, session_state: Optional[dict] = None) -> dict:
    """
    Processes one caller turn end to end.

    session_state carries anything that needs to persist across turns for
    this caller — currently just a pending booking confirmation, if any.
    Pass back whatever this function returns as `session_state` on the
    caller's NEXT turn, so multi-turn flows (like booking confirmation) work.
    """
    session_state = session_state or {}
    pending_booking = session_state.get("pending_booking")

    result = {
        "transcript": transcript,
        "intent": None,
        "escalation": None,
        "tool_called": None,
        "response": None,
        "session_state": {},  # what to pass back in on the next turn
    }
    # ... right before returning the result in ANY of the steps ...

    # STEP 0 — Security: Prompt Injection Guardrail Pre-Check
    # ---------------------------------------------------------------
    guardrail_check = validate_prompt(transcript)
    if not guardrail_check["safe"]:
        result["escalation"] = "prompt_injection"
        result["response"] = (
            "I can only help with business inquiries, scheduling, and standard questions."
        )
        trace_turn(
            transcript=result["transcript"],
            response=result["response"],
            intent=result.get("intent"),
            escalation=result.get("escalation"),
            tool_called=result.get("tool_called"),
        )
        return result
    # ---------------------------------------------------------------
    # STEP 1 — Escalation check runs FIRST and short-circuits everything.
    # This is deliberate priority: a frustrated/human-request/off-topic
    # message should never fall through to booking or knowledge logic.
    # ---------------------------------------------------------------
    escalation_category = await check_escalation(transcript)
    if escalation_category != "none":
        result["escalation"] = escalation_category
        result["response"] = get_escalation_response(escalation_category)
        # Escalation clears any pending booking — start fresh after a handoff.
        trace_turn(
        transcript=result["transcript"],
        response=result["response"],
        intent=result.get("intent"),
        escalation=result.get("escalation"),
        tool_called=result.get("tool_called")
        )
        return result

    # ---------------------------------------------------------------
    # STEP 2 — If a booking confirmation is pending, this turn is the
    # caller's reply to "is that right?" — handle it before anything else.
    # ---------------------------------------------------------------
    if pending_booking:
        reply_type = classify_confirmation_reply(transcript)

        if reply_type == "confirmed":
            tool_result = await execute_tool("request_booking", pending_booking)
            result["tool_called"] = tool_result
            result["response"] = (
                f"Great, you're all set for {pending_booking['service']} on "
                f"{pending_booking['date']} at {pending_booking['time']}!"
            )
            trace_turn(
            transcript=result["transcript"],
            response=result["response"],
            intent=result.get("intent"),
            escalation=result.get("escalation"),
            tool_called=result.get("tool_called")
            )
            return result  # session_state stays empty — booking is done

        if reply_type == "rejected":
            result["response"] = "No problem, let me know if you'd like to book something else."
            trace_turn(
            transcript=result["transcript"],
            response=result["response"],
            intent=result.get("intent"),
            escalation=result.get("escalation"),
            tool_called=result.get("tool_called")
            )
            return result  # clear pending booking

        if reply_type == "correction":
            # Caller changed just one detail (e.g. "actually make it
            # Wednesday at 4"). Merge whatever they mentioned onto the
            # EXISTING pending_booking rather than re-extracting a whole new
            # request from scratch — the old approach called decide_tool_call
            # on the bare correction text, which has no service/date/time of
            # its own most of the time, and produced "service": "unknown"
            # placeholders instead of keeping the original service.
            merged_decision = await decide_correction(transcript, pending_booking)
            if merged_decision:
                booking = merged_decision["arguments"]
                result["response"] = create_booking_confirmation(
                    booking["service"], booking["date"], booking["time"]
                )
                result["session_state"] = {"pending_booking": booking}
                trace_turn(
                transcript=result["transcript"],
                response=result["response"],
                intent=result.get("intent"),
                escalation=result.get("escalation"),
                tool_called=result.get("tool_called")
                )
                return result
            # Couldn't extract anything usable from the correction — ask
            # again, but keep the existing pending booking intact rather
            # than discarding it.
            result["response"] = (
                "Sorry, what would you like to change it to?"
            )
            result["session_state"] = {"pending_booking": pending_booking}
            trace_turn(
            transcript=result["transcript"],
            response=result["response"],
            intent=result.get("intent"),
            escalation=result.get("escalation"),
            tool_called=result.get("tool_called")
            )
            return result

        # ambiguous — re-ask rather than guessing
        result["response"] = (
            f"Sorry, just to confirm — {pending_booking['service']} on "
            f"{pending_booking['date']} at {pending_booking['time']}, is that a yes?"
        )
        result["session_state"] = {"pending_booking": pending_booking}
        trace_turn(
        transcript=result["transcript"],
        response=result["response"],
        intent=result.get("intent"),
        escalation=result.get("escalation"),
        tool_called=result.get("tool_called")
        )
        return result

    # ---------------------------------------------------------------
    # STEP 3 — No escalation, no pending confirmation: classify intent.
    # ---------------------------------------------------------------
    intent_result = await classify_intent(transcript)
    intent = intent_result["intent"]
    result["intent"] = intent

    # ---------------------------------------------------------------
    # STEP 4a — Booking-type intent: try to extract a complete request.
    # ---------------------------------------------------------------
    if intent == "booking":
        decision = await decide_tool_call(transcript)
        if decision:
            booking = decision["arguments"]
            result["response"] = create_booking_confirmation(
                booking["service"], booking["date"], booking["time"]
            )
            result["session_state"] = {"pending_booking": booking}
            trace_turn(
            transcript=result["transcript"],
            response=result["response"],
            intent=result.get("intent"),
            escalation=result.get("escalation"),
            tool_called=result.get("tool_called")
            ) 
            return result
        # Intent says booking, but couldn't extract full details — ask for them.
        result["response"] = await generate_response(
            user_message=transcript,
            base_prompt=SYSTEM_PROMPT,
            knowledge=None,
        )
         
        trace_turn(
        transcript=result["transcript"],
        response=result["response"],
        intent=result.get("intent"),
        escalation=result.get("escalation"),
        tool_called=result.get("tool_called")
        )
        return result

    # ---------------------------------------------------------------
    # STEP 4b — FAQ-type intent: look up knowledge, answer from it only.
    # (This now also covers what used to be separate "insurance"/"pricing"/
    # "location" intents — the classifier collapses those into
    # faq_question, since this is the only branch wired to KB retrieval.)
    # ---------------------------------------------------------------
    if intent == "faq_question":
        knowledge = get_context(transcript, SAMPLE_KNOWLEDGE)
        result["response"] = await generate_response(
            user_message=transcript,
            base_prompt=SYSTEM_PROMPT,
            knowledge=knowledge,
        )
        trace_turn(
        transcript=result["transcript"],
        response=result["response"],
        intent=result.get("intent"),
        escalation=result.get("escalation"),
        tool_called=result.get("tool_called")
        )
        return result

    # ---------------------------------------------------------------
    # STEP 4c — Everything else: plain conversational response.
    # (greeting, goodbye, cancel, reschedule, ordering, order_modification,
    #  complaint, unknown — Milestone 1 doesn't build dedicated handlers
    #  for all of these yet; they get a normal reply for now.)
    # ---------------------------------------------------------------
    result["response"] = await generate_response(
        user_message=transcript,
        base_prompt=SYSTEM_PROMPT,
        knowledge=None,
    )
    trace_turn(
        transcript=result["transcript"],
        response=result["response"],
        intent=result.get("intent"),
        escalation=result.get("escalation"),
        tool_called=result.get("tool_called")
    )
    return result