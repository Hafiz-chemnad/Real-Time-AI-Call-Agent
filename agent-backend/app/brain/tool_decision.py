import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from app.brain.router import get_model_for_task
from app.tools.mcp.schema_builder import BookingRequest

logger = logging.getLogger(__name__)

_BOOKING = re.compile(r"\b(book|schedule|reserve|set up|appointment|come in)\b", re.I)
_DATE = re.compile(
    r"\b(today|tomorrow|(?:(?:this|next)\s+)?(?:mon|tues|wednes|thurs|fri|satur|sun)day|"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?|"
    r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b",
    re.I,
)
_SERVICE = (
    re.compile(
        r"\b(?:book|schedule|reserve|set up|get)\s+(?:me\s+|an?\s+|my\s+)*"
        r"(.+?)(?:\s+(?:appointment|session|visit))?\s+(?:for|on)\s+",
        re.I,
    ),
    re.compile(r"\bcome in for\s+(.+?)\s+(?:for|on)\s+", re.I),
    re.compile(
        r"\bneed\s+(?:to book\s+)?(?:an?\s+)?(.+?)\s+(?:appointment\s+)?(?:for|on)\s+",
        re.I,
    ),
)
_TIME = re.compile(
    r"\b(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)|noon|midnight|\d{1,2}:\d{2}|\d{1,2})\b",
    re.I,
)
_PROMPT = (
    'Return JSON only. Return {"is_booking":true,"service":"...","date":"...","time":"..."} '
    "ONLY if the caller's message explicitly states all three of: what service/appointment type, "
    "what date, and what time. If ANY of these three is not explicitly mentioned in the message, "
    'return {"is_booking":false} — do not guess, infer, or fill in a placeholder value like '
    '"unknown" or "general" for a missing field.'
)

# Used only for corrections to an already-pending booking — the caller may
# mention just a new date/time/service, not a full new request. We must not
# require all three fields here, and must not invent placeholders for the
# ones not mentioned (that's what caused "service": "unknown" bugs before).
_CORRECTION_PROMPT = (
    "The caller is correcting a detail of a booking already in progress. "
    "Return JSON only, containing ONLY the fields the caller actually "
    'mentioned in this message — any of "service", "date", "time". '
    "Do not include a field if it wasn't mentioned. Do not guess or invent "
    'a value. Example: {"time":"4:00 PM"} if only the time was corrected. '
    "If nothing usable was mentioned, return {}."
)


async def _call_llm(**kwargs: Any) -> tuple[Any, str]:
    from app.brain.gateway import call_llm

    return await call_llm(**kwargs)


_PLACEHOLDER_VALUES = {"unknown", "n/a", "na", "tbd", "not specified", "none", "general", "unspecified"}

def _validated(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or payload.get("is_booking") is not True:
        return None
    try:
        booking = BookingRequest.model_validate(payload)
    except ValidationError as exc:
        logger.debug("tool_decision: LLM payload failed validation: %s", exc)
        return None
    values = booking.model_dump()
    if any(v.strip().lower() in _PLACEHOLDER_VALUES for v in values.values()):
        logger.warning("tool_decision: LLM returned placeholder value(s): %s", values)
        return None
    return {"tool": "request_booking", "arguments": values}


def _parse_json_content(content: str) -> Any:
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", content.strip(), re.S | re.I)
    return json.loads(fenced.group(1) if fenced else content)


def _fallback(transcript: str) -> dict[str, Any] | None:
    if not _BOOKING.search(transcript):
        return None
    date = _DATE.search(transcript)
    time = _TIME.search(transcript)
    service = next((match for pattern in _SERVICE if (match := pattern.search(transcript))), None)
    if not date or not time or not service:
        return None
    value = re.sub(
        r"\s+(appointment|session|visit)$", "", service.group(1).strip(" ,.-"), flags=re.I
    )
    try:
        booking = BookingRequest(
            service=value,
            date=date.group(0),
            time=re.sub(r"^at\s+", "", time.group(0), flags=re.I),
        )
    except ValidationError as exc:
        logger.debug("tool_decision: regex fallback failed validation: %s", exc)
        return None
    return {"tool": "request_booking", "arguments": booking.model_dump()}


async def decide_tool_call(transcript: str) -> dict[str, Any] | None:
    """
    Extracts a *complete* new booking request from a transcript.

    Returns a dict with a "source" field ("llm" or "regex_fallback") so
    callers/logs can tell which extraction path actually produced the
    result — useful for verifying whether response_format is honored by
    the underlying provider, since failures silently fall through to regex.
    """
    if not isinstance(transcript, str) or not transcript.strip():
        return None
    try:
        response, _ = await _call_llm(
            model_name=get_model_for_task("classification"),
            messages=[
                {"role": "system", "content": _PROMPT},
                {"role": "user", "content": transcript},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = response.choices[0].message.content
        result = _validated(_parse_json_content(content))
        if result:
            result["source"] = "llm"
            return result
    except (AttributeError, IndexError, TypeError, json.JSONDecodeError) as exc:
        logger.warning(
            "decide_tool_call: LLM path failed (%s: %s), falling back to regex extraction",
            type(exc).__name__,
            exc,
        )
    except Exception:
        logger.exception(
            "decide_tool_call: unexpected error calling LLM, falling back to regex extraction"
        )

    result = _fallback(transcript)
    if result:
        result["source"] = "regex_fallback"
    return result


async def decide_correction(
    transcript: str, existing_booking: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Extracts ONLY the fields the caller mentioned while correcting a booking
    already in progress, and merges them onto `existing_booking`. Never
    invents a value for a field that wasn't mentioned — unmentioned fields
    keep their prior value from `existing_booking`.

    Returns the same shape as decide_tool_call: {"tool", "arguments", "source"}.
    Returns None only if nothing usable could be merged at all (existing
    booking is already incomplete AND nothing new was extracted).
    """
    if not isinstance(transcript, str) or not transcript.strip():
        return None

    partial: dict[str, Any] = {}
    source = "regex_fallback"

    try:
        response, _ = await _call_llm(
            model_name=get_model_for_task("classification"),
            messages=[
                {"role": "system", "content": _CORRECTION_PROMPT},
                {"role": "user", "content": transcript},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = response.choices[0].message.content
        parsed = _parse_json_content(content)
        if isinstance(parsed, dict):
            partial = {
                k: v
                for k, v in parsed.items()
                if k in ("service", "date", "time") and isinstance(v, str) and v.strip()
            }
            source = "llm"
    except (AttributeError, IndexError, TypeError, json.JSONDecodeError) as exc:
        logger.warning(
            "decide_correction: LLM path failed (%s: %s), falling back to regex extraction",
            type(exc).__name__,
            exc,
        )
    except Exception:
        logger.exception(
            "decide_correction: unexpected error calling LLM, falling back to regex extraction"
        )

    if not partial:
        # Regex fallback: only pull whichever of date/time/service is
        # actually present — do NOT require all three like _fallback() does,
        # since a correction message legitimately mentions just one field.
        date = _DATE.search(transcript)
        time = _TIME.search(transcript)
        service = next((m for pattern in _SERVICE if (m := pattern.search(transcript))), None)
        if date:
            partial["date"] = date.group(0)
        if time:
            partial["time"] = re.sub(r"^at\s+", "", time.group(0), flags=re.I)
        if service:
            partial["service"] = re.sub(
                r"\s+(appointment|session|visit)$", "", service.group(1).strip(" ,.-"), flags=re.I
            )

    if not partial:
        return None  # nothing usable mentioned at all

    merged = {**existing_booking, **partial}

    try:
        booking = BookingRequest.model_validate(merged)
    except ValidationError as exc:
        logger.debug("decide_correction: merged booking failed validation: %s", exc)
        return None

    return {"tool": "request_booking", "arguments": booking.model_dump(), "source": source}