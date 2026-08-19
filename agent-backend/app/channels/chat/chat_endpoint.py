import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.api.deps import get_target_business
from app.brain.orchestrator import process_turn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/businesses/{business_id}/chat", tags=["chat"])

# Schemas for the chat endpoint
class ChatRequest(BaseModel):
    transcript: str
    session_state: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    transcript: str
    intent: Optional[str] = None
    escalation: Optional[str] = None
    tool_called: Optional[Dict[str, Any]] = None
    response: Optional[str] = None
    session_state: Dict[str, Any]

@router.post("/", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest,
    business_id: uuid.UUID = Depends(get_target_business)
):
    """
    Text-only endpoint for the dashboard's test-chat widget.
    Bypasses STT and TTS, sending text directly into the AI orchestrator brain.
    """
    try:
        # Call the single-pass orchestrator you already built
        result = await process_turn(
            transcript=request.transcript,
            session_state=request.session_state,
            business_id=str(business_id)
        )
        return result
    except Exception as e:
        logger.exception(f"Chat endpoint error for business {business_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))