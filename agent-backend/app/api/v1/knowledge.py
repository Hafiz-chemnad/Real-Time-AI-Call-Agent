import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_target_business
from app.schemas.knowledge import KnowledgeBaseUpdate, KnowledgeBaseResponse
from app.services import knowledge_service
from app.domain.business_config import invalidate_business_cache

router = APIRouter(prefix="/businesses/{business_id}/knowledge", tags=["knowledge"])

@router.get("/", response_model=KnowledgeBaseResponse)
async def get_knowledge(business_id: uuid.UUID = Depends(get_target_business), db: AsyncSession = Depends(get_db)):
    kb = await knowledge_service.get_knowledge_base(db, business_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not configured yet.")
    return kb

@router.put("/", response_model=KnowledgeBaseResponse)
async def update_knowledge(kb_in: KnowledgeBaseUpdate, business_id: uuid.UUID = Depends(get_target_business), db: AsyncSession = Depends(get_db)):
    result = await knowledge_service.upsert_knowledge_base(db, business_id, kb_in)
    invalidate_business_cache(str(business_id))
    return result