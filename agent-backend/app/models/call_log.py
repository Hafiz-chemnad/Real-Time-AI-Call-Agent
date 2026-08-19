from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base

class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    channel = Column(
        String(20), 
        CheckConstraint("channel IN ('phone', 'chat', 'voice_web', 'whatsapp')"), 
        nullable=False, 
        default="phone"
    )
    
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Store dynamic JSON data for observability
    tools_called = Column(JSONB, nullable=True)
    latency_metrics = Column(JSONB, nullable=True)
    
    # Track safety and human hand-offs
    escalated = Column(Boolean, nullable=False, default=False)
    escalation_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)