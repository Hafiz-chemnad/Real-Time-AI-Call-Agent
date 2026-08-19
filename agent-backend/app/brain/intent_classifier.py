from app.brain.gateway import call_llm
from app.brain.router import get_model_for_task
import re

INTENTS = [
    "greeting", "booking", "cancel", "reschedule", "ordering",
    "order_modification", "faq_question", "complaint", "escalation",
    "goodbye", "unknown",
]

_SYSTEM_CONTENT = """
You are an intent classification AI.

Classify the user's message into EXACTLY ONE of these intents.

- greeting: greetings like hello, hi
- goodbye: goodbye or thank you
- booking: making a new booking or appointment
- cancel: cancelling an appointment or reservation
- reschedule: changing appointment date or time
- ordering: placing a new food or product order
- order_modification: cancelling or modifying an existing order
- faq_question: any general question the business can answer from its own
  information — this includes pricing, insurance accepted, hours, location/
  address, parking, menu/services, policies, and anything similar.
- complaint: unhappy/frustrated but NOT asking to speak to another person.
- escalation: explicitly requests a human agent, manager, supervisor, or support.
- unknown: unrelated or unclear requests

Priority Rules:
- If the user is making a booking, cancellation, rescheduling, or ordering request,
  classify according to the requested action even if they also express frustration.
- Only return "complaint" if the main purpose is to complain with no actionable request.
- Only return "escalation" if explicitly asking for a human.
- If the message is a short/ambiguous reply (e.g. "Monday", "yeah", "the 3pm one"),
  use the recent conversation to understand what it's answering, and classify
  accordingly rather than defaulting to "unknown".

Return ONLY the intent name.
"""


class IntentClassifier:
    async def classify(self, message: str, chat_history: list | None = None):
        messages = [{"role": "system", "content": _SYSTEM_CONTENT}]
        if chat_history:
            messages.extend(chat_history[-4:])
        messages.append({"role": "user", "content": message})

        response, _ = await call_llm(
            model_name=get_model_for_task("classification"),
            messages=messages,
            temperature=0,
        )

        intent = response.choices[0].message.content.strip().lower()
        intent = re.sub(r"[^a-z_]", "", intent)

        aliases = {
            "faq": "faq_question", "order": "ordering",
            "modify_order": "order_modification", "complaints": "complaint",
            "insurance": "faq_question", "pricing": "faq_question", "location": "faq_question",
        }
        intent = aliases.get(intent, intent)
        if intent not in INTENTS:
            intent = "unknown"
        return {"intent": intent}


_classifier = IntentClassifier()


async def classify_intent(message: str, chat_history: list | None = None):
    return await _classifier.classify(message, chat_history)