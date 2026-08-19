from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base


class Tool(Base):
    __tablename__ = "tools"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    tool_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    execution_type = Column(
        String(20),
        CheckConstraint("execution_type IN ('api', 'webhook')"),
        nullable=False,
    )
    parameters = Column(JSONB, nullable=False)

    # used when execution_type = 'api'
    url = Column(Text, nullable=True)
    method = Column(String(10), nullable=True)
    auth_config = Column(JSONB, nullable=True)
    body_template = Column(JSONB, nullable=True)

    # used when execution_type = 'webhook'
    webhook_url = Column(Text, nullable=True)

    requires_confirmation = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)