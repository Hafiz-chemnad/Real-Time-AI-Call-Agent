# app/brain/orchestrator.py

from app.brain.gateway import call_llm
from app.brain.router import get_model_for_task

SYSTEM_PROMPT = (
    "You are a friendly, professional receptionist answering calls for a business. "
    "Keep responses short and conversational, like a real front-desk person would speak "
    "on the phone — not an essay. Usually 1-2 sentences. No headers, no bullet points, "
    "no markdown formatting. Just talk naturally."
)


async def process_turn(transcript: str) -> dict:
    """
    Minimal stub — will grow as Person B and Person C's pieces are integrated.
    Currently: just sends the transcript straight to the main model and returns a reply.
    No intent classification, no knowledge lookup, no tool-calling yet.
    """
    model_name = get_model_for_task("conversation")

    response, actual_model = await call_llm(
        model_name=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
    )

    return {
        "transcript": transcript,
        "intent": None,          # placeholder — Person B's classifier plugs in here
        "tool_called": None,     # placeholder — Person C's tool decision plugs in here
        "response": response.choices[0].message.content,
        "model_used": actual_model,
    }