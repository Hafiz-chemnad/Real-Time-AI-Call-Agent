from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    tone = Column(String(100), nullable=True)
    hours = Column(Text, nullable=True)
    transfer_numbers = Column(JSONB, nullable=True)
    knowledge_mode = Column(String(20), nullable=False, default="vectorless")
    business_type = Column(String(20), nullable=False, default="general")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)