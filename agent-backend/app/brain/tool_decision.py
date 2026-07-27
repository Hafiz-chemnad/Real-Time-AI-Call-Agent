import json
import re
from typing import Any

from pydantic import ValidationError

from app.brain.router import get_model_for_task
from app.tools.mcp.schema_builder import BookingRequest

_BOOKING = re.compile(r"\b(book|schedule|reserve|set up|appointment|come in)\b", re.I)
_DATE = re.compile(
    r"\b(today|tomorrow|(?:(?:this|next)\s+)?(?:mon|tues|wednes|thurs|fri|satur|sun)day|"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?|"
    r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b",
    re.I,
)
_TIME = re.compile(
    r"\b(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)|noon|midnight|\d{1,2}:\d{2})\b",
    re.I,
)
_SERVICE = (
    re.compile(
        r"\b(?:book|schedule|reserve|set up)\s+(?:me\s+|an?\s+|my\s+)*"
        r"(.+?)(?:\s+(?:appointment|session|visit))?\s+(?:for|on)\s+",
        re.I,
    ),
    re.compile(r"\bcome in for\s+(.+?)\s+(?:for|on)\s+", re.I),
    re.compile(
        r"\bneed\s+(?:to book\s+)?(?:an?\s+)?(.+?)\s+(?:appointment\s+)?(?:for|on)\s+",
        re.I,
    ),
)
_PROMPT = (
    'Return JSON only. For a complete booking request return {"is_booking":true,'
    '"service":"...","date":"...","time":"..."}. Otherwise return {"is_booking":false}.'
)


async def _call_llm(**kwargs: Any) -> tuple[Any, str]:
    from app.brain.gateway import call_llm

    return await call_llm(**kwargs)


def _validated(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or payload.get("is_booking") is not True:
        return None
    try:
        booking = BookingRequest.model_validate(payload)
    except ValidationError:
        return None
    return {"tool": "request_booking", "arguments": booking.model_dump()}


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
    except ValidationError:
        return None
    return {"tool": "request_booking", "arguments": booking.model_dump()}


async def decide_tool_call(transcript: str) -> dict[str, Any] | None:
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
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", content.strip(), re.S | re.I)
        result = _validated(json.loads(fenced.group(1) if fenced else content))
        if result:
            return result
    except (AttributeError, IndexError, TypeError, json.JSONDecodeError, Exception):
        pass
    return _fallback(transcript)
