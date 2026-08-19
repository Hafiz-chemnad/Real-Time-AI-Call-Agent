from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class CallLogBase(BaseModel):
    channel: str = Field(default="phone", pattern="^(phone|chat|voice_web|whatsapp)$")
    transcript: Optional[str] = None
    summary: Optional[str] = None
    tools_called: Optional[Dict[str, Any]] = None
    latency_metrics: Optional[Dict[str, Any]] = None
    escalated: bool = False
    escalation_reason: Optional[str] = None

class CallLogCreate(CallLogBase):
    business_id: UUID

class CallLogResponse(CallLogBase):
    id: UUID
    business_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)