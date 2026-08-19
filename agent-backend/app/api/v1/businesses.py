import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.deps import get_db, get_target_business
from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessResponse
from app.schemas.business import BusinessUpdate
from app.schemas.prompt import PromptUpdate, PromptResponse
from app.schemas.guardrail import GuardrailUpdate, GuardrailResponse
from app.services import business_service
from app.domain.business_config import invalidate_business_cache

router = APIRouter(prefix="/businesses", tags=["businesses"])

@router.post("/", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(business_in: BusinessCreate, db: AsyncSession = Depends(get_db)):
    """Called by the Next.js dashboard when a new user signs up and creates their business."""
    new_business = Business(**business_in.model_dump())
    db.add(new_business)
    await db.commit()
    await db.refresh(new_business)
    return new_business

@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(business_id: uuid.UUID = Depends(get_target_business), db: AsyncSession = Depends(get_db)):
    """Fetches the business settings for the dashboard."""
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

@router.put("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_in: BusinessUpdate, 
    business_id: uuid.UUID = Depends(get_target_business), 
    db: AsyncSession = Depends(get_db)
):
    """Updates core business details (hours, tone, transfer numbers, etc.)."""
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    for key, value in business_in.model_dump(exclude_unset=True).items():
        setattr(business, key, value)
        
    await db.commit()
    await db.refresh(business)
    invalidate_business_cache(str(business_id))
    return business



@router.put("/{business_id}/prompt", response_model=PromptResponse)
async def update_prompt(
    prompt_in: PromptUpdate, 
    business_id: uuid.UUID = Depends(get_target_business), 
    db: AsyncSession = Depends(get_db)
):
    """Updates or creates the system prompt for a business."""
    result = await business_service.upsert_system_prompt(str(business_id), prompt_in.system_prompt_template, db)
    invalidate_business_cache(str(business_id))
    return result
@router.put("/{business_id}/guardrails", response_model=GuardrailResponse)
async def update_guardrails(
    guardrail_in: GuardrailUpdate, 
    business_id: uuid.UUID = Depends(get_target_business), 
    db: AsyncSession = Depends(get_db)
):
    """Updates or creates the guardrails for a business."""
    result = await business_service.upsert_guardrail_config(str(business_id), guardrail_in.model_dump(exclude_unset=True), db)
    invalidate_business_cache(str(business_id))
    return result