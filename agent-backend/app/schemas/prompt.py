from pydantic import BaseModel, ConfigDict
from uuid import UUID

class PromptUpdate(BaseModel):
    system_prompt_template: str

class PromptResponse(PromptUpdate):
    id: UUID
    business_id: UUID
    
    model_config = ConfigDict(from_attributes=True)