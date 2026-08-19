from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base

class Guardrail(Base):
    __tablename__ = "guardrails"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), unique=True, nullable=False)
    
    scope = Column(String, nullable=True)
    out_of_scope_response = Column(String, nullable=True)
    require_confirmation_for = Column(JSONB, nullable=True)
    escalate_on = Column(JSONB, nullable=True)
    never_reveal = Column(JSONB, nullable=True)
    no_hallucination_instruction = Column(String, nullable=True)
    pii_handling_instruction = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)