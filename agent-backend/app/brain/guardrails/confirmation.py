import re
import logging
from typing import Literal

from app.tools.mcp.schema_builder import BookingRequest
from app.brain.gateway import call_llm

logger = logging.getLogger(__name__)

ConfirmationResult = Literal["confirmed", "rejected", "correction", "ambiguous"]

# TIER 1: English STRICT Matches
_EN_STRICT_CONFIRM = re.compile(
    r"^\s*(yes|yeah|yep|yup|sure|correct|that'?s right|that\s+is\s+right|that'?s correct|that\s+is\s+correct|sounds good|ok|okay|go ahead|perfect|please|proceed|confirm|looks good|please do|do it)[\s,.!]*(proceed|go ahead|continue|please|thanks|thank you|do it|that'?s (correct|right)|that\s+is\s+(correct|right))?\s*[.!?\s]*$", 
    re.I
)
_EN_STRICT_REJECT = re.compile(r"^\s*(no|nope|nah|cancel|never mind|forget it|stop)\s*[.!?\s]*$", re.I)

# TIER 1: Malayalam STRICT Matches (Manglish & Native Script)
_ML_STRICT_CONFIRM = re.compile(
    r"^\s*(athe|aam|shari|kuzhappamilla|cheyyam|ok|okay|yes|pinne|theerchayayum|അതെ|ശരി|കുഴപ്പമില്ല|ചെയ്യാം|പിന്നെ|തീർച്ചയായും|ഓക്കേ|ഓക്കെ|കൊണ്ടുപോയിക്കോളൂ)[\s,.!]*(proceed|go ahead|please|thanks|thank you|do it|cheyyam|ശരി|കൊണ്ടുപോയിക്കോളൂ)?\s*[.!?\s]*$",
    re.I
)
_ML_STRICT_CONFIRM = re.compile(
    r"^\s*(athe|aam|shari|kuzhappamilla|cheyyam|ok|okay|yes|pinne|theerchayayum|അതെ|ശരി|കുഴപ്പമില്ല|ചെയ്യാം|പിന്നെ|തീർച്ചയായും|ഓക്കേ|ഓക്കെ|കൊണ്ടുപോയിക്കോളൂ)[\s,.!]*(proceed|go ahead|continue|please|thanks|thank you|do it|cheyyam|ശരി|കൊണ്ടുപോയിക്കോളൂ|മുന്നോട്ട് പൊയ്ക്കോളൂ|മുന്നോട്ട് പോകാം)?\s*[.!?\s]*$",
    re.I
)

def create_booking_confirmation(
    service: str | BookingRequest,
    date: str | None = None,
    time: str | None = None,
) -> str:
    booking = (
        service
        if isinstance(service, BookingRequest)
        else BookingRequest(service=service, date=date, time=time)
    )
    return (
        f"Just to confirm, would you like me to request your {booking.service} "
        f"appointment for {booking.date} at {booking.time}?"
    )


async def classify_confirmation_reply(reply: str, call_language: str = "mixed") -> ConfirmationResult:
    """
    3-Tier Confirmation Router:
    1. 0ms Regex Match (Exact common confirmations/rejections in EN/ML).
    2. Ultra-fast 1-token LLM Classifier (~200ms) to semantically detect confirmation vs correction.
    3. Safe Ambiguous Fallback.
    """
    if not isinstance(reply, str) or not reply.strip():
        return "ambiguous"

    cleaned_reply = reply.strip()

    # TIER 1: 0ms Exact Match Fast-Path
    if call_language in ("en", "mixed"):
        if _EN_STRICT_CONFIRM.match(cleaned_reply):
            return "confirmed"
        if _EN_STRICT_REJECT.match(cleaned_reply):
            return "rejected"

    if call_language in ("ml", "mixed"):
        if _ML_STRICT_CONFIRM.match(cleaned_reply):
            return "confirmed"
        if _ML_STRICT_REJECT.match(cleaned_reply):
            return "rejected"

    # TIER 2: Fast 1-Token Semantic Safety Net
    # TIER 2: Fast 1-Token Semantic Safety Net
    prompt = (
        "You are an intent classifier for a voice booking receptionist.\n"
        "The assistant asked the caller to confirm booking details.\n"
        f"Caller reply: \"{cleaned_reply}\"\n\n"
        "Classify the caller's intent into EXACTLY ONE of these categories:\n"
        "- CONFIRMED: Caller agrees, approves, gives the go-ahead, or says yes/okay in any phrasing or language. Examples: 'Yes, continue', 'അതെ മുന്നോട്ട് പൊയ്ക്കോളൂ', 'ചെയ്യാം'.\n"
        "- REJECTED: Caller declines, cancels, stops, or says no/don't want it.\n"
        "- CORRECTION: Caller wants to alter time, date, service, or provide different booking details.\n"
        "- AMBIGUOUS: Completely unclear, filler noise, or unrelated statement.\n\n"
        "Output ONLY the single category name."
    )

    try:
        response, _ = await call_llm(
            model_name="fast-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5,
        )
        verdict = response.choices[0].message.content.strip().upper()

        if "CONFIRM" in verdict:
            return "confirmed"
        if "REJECT" in verdict:
            return "rejected"
        if "CORRECT" in verdict:
            return "correction"
        return "ambiguous"
    except Exception as e:
        logger.warning(f"Semantic confirmation classifier error: {e}")
        return "correction"