from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from uuid import UUID

class ToolBase(BaseModel):
    tool_name: str
    description: str
    execution_type: str = Field(pattern="^(api|webhook)$")
    parameters: Dict[str, Any]
    
    # API specific fields
    url: Optional[str] = None
    method: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    body_template: Optional[Dict[str, Any]] = None
    
    # Webhook specific fields
    webhook_url: Optional[str] = None
    
    requires_confirmation: bool = False
    is_active: bool = True

class ToolCreate(ToolBase):
    pass

class ToolUpdate(BaseModel):
    tool_name: Optional[str] = None
    description: Optional[str] = None
    execution_type: Optional[str] = Field(None, pattern="^(api|webhook)$")
    parameters: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    method: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    body_template: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = None
    requires_confirmation: Optional[bool] = None
    is_active: Optional[bool] = None

class ToolResponse(ToolBase):
    id: UUID
    business_id: UUID

    model_config = ConfigDict(from_attributes=True)