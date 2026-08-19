from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from uuid import UUID

class BusinessBase(BaseModel):
    name: str
    tone: Optional[str] = None
    hours: Optional[str] = None
    transfer_numbers: Optional[Dict[str, Any]] = None
    knowledge_mode: str = Field(default="vectorless", pattern="^(vectorless|vector)$")
    business_type: str = Field(default="general", pattern="^(delivery|appointment|general)$")

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    tone: Optional[str] = None
    hours: Optional[str] = None
    transfer_numbers: Optional[Dict[str, Any]] = None
    knowledge_mode: Optional[str] = Field(None, pattern="^(vectorless|vector)$")
    business_type: Optional[str] = Field(None, pattern="^(delivery|appointment|general)$")

class BusinessResponse(BusinessBase):
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)