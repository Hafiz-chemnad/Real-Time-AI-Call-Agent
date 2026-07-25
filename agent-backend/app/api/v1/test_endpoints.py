import time
from fastapi import APIRouter
from pydantic import BaseModel
from app.brain.gateway import call_llm
from app.brain.router import get_model_for_task
from app.brain.orchestrator import process_turn

router = APIRouter(prefix="/test", tags=["test"])

SYSTEM_PROMPT = (
    "You are a friendly, professional receptionist answering calls for a business. "
    "Keep responses short and conversational, like a real front-desk person would speak "
    "on the phone — not an essay. Usually 1-2 sentences. No headers, no bullet points, "
    "no markdown formatting. Just talk naturally."
)


class PingRequest(BaseModel):
    message: str
    task_type: str = "conversation"  # "classification" | "conversation" | "fallback"


@router.post("/llm-ping")
async def llm_ping(payload: PingRequest):
    model_name = get_model_for_task(payload.task_type)

    start = time.perf_counter()
    response, actual_model = await call_llm(
        model_name=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": payload.message},
        ],
    )
    elapsed = time.perf_counter() - start

    return {
        "requested_model": model_name,
        "actual_model_used": actual_model,
        "response": response.choices[0].message.content,
        "response_time_seconds": round(elapsed, 3),
    }


class ProcessTurnRequest(BaseModel):
    transcript: str


@router.post("/process-turn")
async def test_process_turn(payload: ProcessTurnRequest):
    return await process_turn(payload.transcript)