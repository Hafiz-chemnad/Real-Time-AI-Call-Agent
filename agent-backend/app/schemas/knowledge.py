from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class KnowledgeBaseBase(BaseModel):
    mode: str = Field(pattern="^(vectorless|vector)$")
    content: Optional[str] = None
    vector_collection_id: Optional[str] = None

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(BaseModel):
    mode: Optional[str] = Field(None, pattern="^(vectorless|vector)$")
    content: Optional[str] = None
    vector_collection_id: Optional[str] = None

class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: UUID
    business_id: UUID

    model_config = ConfigDict(from_attributes=True)