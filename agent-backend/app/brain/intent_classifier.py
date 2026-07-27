from app.brain.gateway import call_llm

INTENTS = [
    "greeting",
    "booking",
    "cancel",
    "reschedule",
    "ordering",
    "order_modification",
    "pricing",
    "insurance",
    "location",
    "faq_question",
    "complaint",
    "escalation",
    "goodbye",
    "unknown",
]


class IntentClassifier:
    def __init__(self):
        pass

    async def classify(self, message: str):

        messages = [
            {
                "role": "system",
                "content": """
You are an intent classification AI.

Classify the user's message into EXACTLY ONE of these intents.

- greeting: greetings like hello, hi
- goodbye: goodbye or thank you
- booking: making a new booking or appointment
- cancel: cancelling an appointment or reservation
- reschedule: changing appointment date or time
- ordering: placing a new food or product order
- order_modification: cancelling or modifying an existing order
- pricing: asking about cost or price
- insurance: asking about insurance
- location: asking about address, branch or delivery area
- faq_question: asking general questions about services, menu, timings, parking, products, etc.
- complaint:
  The user is unhappy, frustrated, or dissatisfied with the service or product,
  but is NOT asking to speak to another person.
- escalation:
  The user explicitly requests a human agent, manager, supervisor,
  customer support, or asks to transfer the conversation.
- unknown: unrelated or unclear requests
Priority Rules:

- If the user is making a booking, cancellation, rescheduling, or ordering request,
  classify according to the requested action even if they also express frustration.

- Only return "complaint" if the main purpose of the message is to complain and
  there is no actionable booking or ordering request.

- Only return "escalation" if the user explicitly asks for a human agent,
  manager, supervisor, or customer support.

Examples:

User: I'm a bit annoyed but I still want to book Tuesday at 3.
Intent: booking

User: I've been waiting 40 minutes.
Intent: complaint

User: I'm unhappy. Connect me to a manager.
Intent: escalation

User: Cancel my appointment.
Intent: cancel

User: Cancel my pizza order.
Intent: order_modification


Return ONLY the intent name.
""",
            },
            {
                "role": "user",
                "content": message,
            },
        ]

        response, _ = await call_llm(
            model_name="fast-model",
            messages=messages,
            temperature=0,
        )

        intent = response.choices[0].message.content.strip().lower()

        aliases = {
            "faq": "faq_question",
            "faq_question": "faq_question",
            "order": "ordering",
            "ordering": "ordering",
            "modify_order": "order_modification",
            "order modification": "order_modification",
            "complaints": "complaint",
        }

        intent = aliases.get(intent, intent)

        if intent not in INTENTS:
            intent = "unknown"

        return {
            "intent": intent
        }


_classifier = IntentClassifier()


async def classify_intent(message: str):
    return await _classifier.classify(message)