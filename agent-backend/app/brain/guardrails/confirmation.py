import re
from typing import Literal

from app.tools.mcp.schema_builder import BookingRequest

ConfirmationResult = Literal["confirmed", "rejected", "correction", "ambiguous"]

# STRICT Matches: It must be just these words and nothing else (punctuation is allowed)
# STRICT Matches: Expanded to allow combinations like "Yes, proceed" or "Sure, thanks"
_STRICT_CONFIRM = re.compile(
    r"^\s*(yes|yeah|yep|yup|sure|correct|that'?s right|that\s+is\s+right|that'?s correct|that\s+is\s+correct|sounds good|ok|okay|go ahead|perfect|please|proceed|confirm|looks good|please do|do it)[\s,.!]*(proceed|go ahead|please|thanks|thank you|do it|that'?s (correct|right)|that\s+is\s+(correct|right))?\s*[.!?\s]*$", 
    re.I
)
_STRICT_REJECT = re.compile(r"^\s*(no|nope|nah|cancel|never mind|forget it|stop)\s*[.!?\s]*$", re.I)


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


def classify_confirmation_reply(reply: str) -> ConfirmationResult:
    if not isinstance(reply, str) or not reply.strip():
        return "ambiguous"

    # 1. Did they say a simple, clean confirmation?
    if _STRICT_CONFIRM.match(reply):
        return "confirmed"

    # 2. Did they say a simple, clean rejection?
    if _STRICT_REJECT.match(reply):
        return "rejected"

    # 3. Everything else (e.g., "Yes, but make it 9", "No, I meant Tuesday", "Actually 10am")
    # is routed as a correction. This passes the full sentence to your decide_correction
    # LLM, which effortlessly extracts the new details.
    return "correction"