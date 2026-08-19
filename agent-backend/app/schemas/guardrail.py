from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from uuid import UUID

class GuardrailUpdate(BaseModel):
    scope: Optional[str] = None
    out_of_scope_response: Optional[str] = None
    require_confirmation_for: Optional[List[Any]] = None 
    escalate_on: Optional[List[Any]] = None
    never_reveal: Optional[List[Any]] = None
    no_hallucination_instruction: Optional[str] = None
    pii_handling_instruction: Optional[str] = None

class GuardrailResponse(GuardrailUpdate):
    id: UUID
    business_id: UUID
    
    model_config = ConfigDict(from_attributes=True)