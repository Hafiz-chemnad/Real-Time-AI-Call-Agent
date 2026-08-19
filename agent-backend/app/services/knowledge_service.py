import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge import KnowledgeBaseUpdate

async def get_knowledge_base(db: AsyncSession, business_id: uuid.UUID) -> KnowledgeBase | None:
    """Fetches the knowledge base configuration for a business."""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.business_id == business_id))
    return result.scalar_one_or_none()

async def upsert_knowledge_base(db: AsyncSession, business_id: uuid.UUID, kb_data: KnowledgeBaseUpdate) -> KnowledgeBase:
    """Updates the knowledge base if it exists, or creates it if it doesn't."""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.business_id == business_id))
    db_kb = result.scalar_one_or_none()
    
    if db_kb:
        # Update existing
        for key, value in kb_data.model_dump(exclude_unset=True).items():
            setattr(db_kb, key, value)
    else:
        # Create new
        db_kb = KnowledgeBase(**kb_data.model_dump(exclude_unset=True), business_id=business_id)
        db.add(db_kb)
        
    await db.commit()
    await db.refresh(db_kb)
    return db_kb