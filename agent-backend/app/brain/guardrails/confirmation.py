import re
from typing import Literal

from app.tools.mcp.schema_builder import BookingRequest

ConfirmationResult = Literal["confirmed", "rejected", "correction", "ambiguous"]

_CORRECTION = re.compile(
    r"\b(wait|actually|instead|change|make that|rather|sorry|i meant)\b", re.I
)
_REJECTION = re.compile(r"^\s*(no|nope|nah|cancel|don't|do not|never mind)\b", re.I)
_CONFIRMATION = re.compile(
    r"^\s*(yes|yeah|yep|yup|sure|correct|that's right|sounds good|ok|okay|go ahead)\b",
    re.I,
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


def classify_confirmation_reply(reply: str) -> ConfirmationResult:
    if not isinstance(reply, str) or not reply.strip():
        return "ambiguous"
    if _CORRECTION.search(reply):
        return "correction"
    if _REJECTION.search(reply):
        return "rejected"
    if _CONFIRMATION.search(reply):
        return "confirmed"
    return "ambiguous"
