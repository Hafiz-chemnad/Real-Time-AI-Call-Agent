import re
from typing import Literal

EscalationCategory = Literal["frustration", "human_request", "off_topic", "none"]

_HUMAN = re.compile(
    r"\b(human|real person|live (person|agent)|representative|operator|manager|supervisor)\b",
    re.I,
)
_FRUSTRATION = re.compile(
    r"\b(furious|livid|unacceptable|ridiculous|fed up|worst (service|experience)|"
    r"third time|this is useless)\b",
    re.I,
)
_OFF_TOPIC = re.compile(
    r"\b(tell me a joke|help me cheat|write my (essay|homework)|"
    r"(buy|sell|trade) (bitcoin|crypto|stocks?)|hack an? account)\b",
    re.I,
)
_RESPONSES = {
    "human_request": "Of course. I’ll help route you to a human representative.",
    "frustration": "I’m sorry this has been so frustrating. I’ll route you to a human representative.",
    "off_topic": "I can help with this business’s services, appointments, and related questions.",
    "none": "",
}


async def check_escalation(transcript: str) -> EscalationCategory:
    if not isinstance(transcript, str) or not transcript.strip():
        return "none"
    if _HUMAN.search(transcript):
        return "human_request"
    if _FRUSTRATION.search(transcript):
        return "frustration"
    if _OFF_TOPIC.search(transcript):
        return "off_topic"
    return "none"


def get_escalation_response(category: EscalationCategory) -> str:
    return _RESPONSES.get(category, "")
