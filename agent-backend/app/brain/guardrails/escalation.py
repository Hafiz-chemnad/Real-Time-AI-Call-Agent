import json
import logging
import re
from typing import Any, Literal

from app.brain.gateway import call_llm
from app.brain.router import get_model_for_task

logger = logging.getLogger(__name__)

EscalationCategory = Literal["frustration", "human_request", "off_topic", "custom_trigger", "none"]

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
    "custom_trigger": "I'm not able to handle that specific request. Let me connect you with someone who can.",
    "none": "",
}

_LLM_PROMPT = """You are a safety classifier for a phone/chat receptionist system.

Classify the caller's message into EXACTLY ONE category:

- human_request: the caller explicitly asks for a human, real person, representative, manager, or supervisor.
- frustration: the caller expresses clear frustration, anger, or dissatisfaction with the service/experience.
- off_topic: the request is totally unrelated to this business's services (e.g., asking for recipes, coding help, jokes). 
  CRITICAL: If the message is a short answer like "Monday", "yeah", or a name, look at the chat history! If it directly answers a question the AI just asked, it is NOT off_topic (return 'none').
- none: none of the above — a normal, on-topic request or a direct answer to a question.

Return ONLY the category name, nothing else."""


def _regex_precheck(transcript: str) -> EscalationCategory | None:
    if _HUMAN.search(transcript):
        return "human_request"
    if _FRUSTRATION.search(transcript):
        return "frustration"
    return None


async def check_escalation(
    transcript: str, custom_triggers: list = None, chat_history: list | None = None
) -> EscalationCategory:
    if not isinstance(transcript, str) or not transcript.strip():
        return "none"

    precheck = _regex_precheck(transcript)
    if precheck:
        return precheck

    dynamic_prompt = _LLM_PROMPT
    if custom_triggers and isinstance(custom_triggers, list) and len(custom_triggers) > 0:
        triggers_str = ", ".join(custom_triggers)
        dynamic_prompt += f"\n- custom_trigger: the caller mentions or asks about any of these business-specific restricted topics: {triggers_str}."

    messages = [{"role": "system", "content": dynamic_prompt}]
    if chat_history:
        messages.extend(chat_history[-4:])
    messages.append({"role": "user", "content": transcript})

    try:
        model_name = get_model_for_task("classification")
        response, _ = await call_llm(model_name=model_name, messages=messages, temperature=0)
        result = response.choices[0].message.content.strip().lower()
        result = re.sub(r"[^a-z_]", "", result)
        if result in ("frustration", "human_request", "off_topic", "custom_trigger", "none"):
            return result
        logger.warning("check_escalation: unexpected LLM output %r, defaulting to 'none'", result)
        return "none"
    except Exception:
        logger.exception("check_escalation: LLM classification failed, falling back to 'none'")
        return "none"

def get_escalation_response(category: EscalationCategory) -> str:
    return _RESPONSES.get(category, "")