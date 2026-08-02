import json
import logging
import re
from typing import Any, Literal

from app.brain.gateway import call_llm
from app.brain.router import get_model_for_task

logger = logging.getLogger(__name__)

EscalationCategory = Literal["frustration", "human_request", "off_topic", "none"]

# Fast pre-check patterns — catch obvious/unambiguous cases cheaply before
# calling the LLM. These are intentionally narrow; the LLM call below is the
# real classifier and handles paraphrasing/variation the regex can't.
_HUMAN = re.compile(
    r"\b(human|real person|live (person|agent)|representative|operator|manager|supervisor)\b",
    re.I,
)
_FRUSTRATION = re.compile(
    r"\b(furious|livid|frustrat\w*|unacceptable|ridiculous|fed up|"
    r"worst (service|experience)|third time|three times|so many times|"
    r"this is useless|no one('?s| has) helped)\b",
    re.I,
)

_RESPONSES = {
    "human_request": "Of course. I’ll help route you to a human representative.",
    "frustration": "I’m sorry this has been so frustrating. I’ll route you to a human representative.",
    "off_topic": "I can help with this business’s services, appointments, and related questions.",
    "none": "",
}

_LLM_PROMPT = """You are a safety classifier for a phone/chat receptionist system.

Classify the caller's message into EXACTLY ONE category:

- human_request: the caller explicitly asks for a human, real person, representative, manager, or supervisor.
- frustration: the caller expresses clear frustration, anger, or dissatisfaction with the service/experience (e.g. "I've called three times", "this is ridiculous", "I'm so frustrated").
- off_topic: the request is unrelated to this business's services (general knowledge questions, requests to write essays, jokes, financial/crypto advice, hacking, or anything with no connection to the business).
- none: none of the above — a normal, on-topic request (including mild annoyance that doesn't rise to real frustration, e.g. "ugh, ok whatever, can you just book it").

Return ONLY the category name, nothing else."""


def _regex_precheck(transcript: str) -> EscalationCategory | None:
    """Cheap, narrow pre-check for unambiguous cases. Returns None if uncertain,
    in which case the caller should fall through to the LLM classifier."""
    if _HUMAN.search(transcript):
        return "human_request"
    if _FRUSTRATION.search(transcript):
        return "frustration"
    return None


async def check_escalation(transcript: str) -> EscalationCategory:
    if not isinstance(transcript, str) or not transcript.strip():
        return "none"

    precheck = _regex_precheck(transcript)
    if precheck:
        return precheck

    try:
        model_name = get_model_for_task("classification")
        response, _ = await call_llm(
            model_name=model_name,
            messages=[
                {"role": "system", "content": _LLM_PROMPT},
                {"role": "user", "content": transcript},
            ],
            temperature=0,
        )
        result = response.choices[0].message.content.strip().lower()
        result = re.sub(r"[^a-z_]", "", result)
        if result in ("frustration", "human_request", "off_topic", "none"):
            return result  # type: ignore[return-value]
        logger.warning("check_escalation: unexpected LLM output %r, defaulting to 'none'", result)
        return "none"
    except Exception:
        logger.exception("check_escalation: LLM classification failed, falling back to 'none'")
        return "none"


def get_escalation_response(category: EscalationCategory) -> str:
    return _RESPONSES.get(category, "")