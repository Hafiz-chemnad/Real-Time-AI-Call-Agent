import re

# Order matters: check more specific patterns (email, card) before broader
# ones (phone) so a card number embedded near other digits isn't partially
# caught by the phone regex first.

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Card-like: 13-19 digits, optionally grouped with spaces/dashes
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")

# Phone numbers: matches common spoken/written formats picked up by STT,
# e.g. "917 994 1347 64", "(917) 994-1347", "+91 9179941347"
_PHONE_RE = re.compile(
    r"(\+?\d{1,3}[ -]?)?(\(?\d{3}\)?[ -]?)?\d{3}[ -]?\d{4}(?:[ -]?\d{2,4})?"
)

# US-style SSN pattern (also loosely catches similar national ID formats)
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def redact_pii(text: str) -> str:
    """
    Best-effort redaction of common PII patterns (email, phone, card-like
    numbers, SSN-like numbers) before a transcript is persisted to
    call_logs or sent to Langfuse. This is a defense-in-depth measure, not
    a guarantee — free-text callers can state PII in ways no regex catches
    (e.g. spelling out a name, describing a symptom). Treat this as
    reducing exposure, not eliminating it entirely.
    """
    if not isinstance(text, str) or not text:
        return text

    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = _SSN_RE.sub("[REDACTED_ID]", redacted)
    redacted = _CARD_RE.sub("[REDACTED_CARD]", redacted)
    redacted = _PHONE_RE.sub("[REDACTED_PHONE]", redacted)

    return redacted