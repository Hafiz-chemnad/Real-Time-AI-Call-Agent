import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.prompt import Prompt
from app.models.guardrail import Guardrail
from app.models.knowledge_base import KnowledgeBase
from app.models.tool import Tool


def _parse_uuid(business_id: str):
    try:
        return uuid.UUID(business_id) if isinstance(business_id, str) else business_id
    except ValueError:
        return None


async def get_system_prompt(business_id: str, session: AsyncSession) -> str | None:
    target_uuid = _parse_uuid(business_id)
    if target_uuid is None:
        return None
    result = await session.execute(
        select(Prompt.system_prompt_template).where(Prompt.business_id == target_uuid)
    )
    return result.scalar_one_or_none()


async def get_guardrail_config(business_id: str, session: AsyncSession) -> Guardrail | None:
    target_uuid = _parse_uuid(business_id)
    if target_uuid is None:
        return None
    result = await session.execute(
        select(Guardrail).where(Guardrail.business_id == target_uuid)
    )
    return result.scalar_one_or_none()


async def get_business_knowledge(business_id: str, session: AsyncSession) -> dict | None:
    target_uuid = _parse_uuid(business_id)
    if target_uuid is None:
        return None
    result = await session.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.business_id == target_uuid
        )
    )
    kb_record = result.scalar_one_or_none()
    if kb_record:
        # Return both content and mode so the selector knows how to handle it
        return {
            "mode": kb_record.mode,
            "content": kb_record.content,
            "vector_collection_id": kb_record.vector_collection_id
        }
    return None


async def get_business_tools(business_id: str, session: AsyncSession) -> list[Tool]:
    target_uuid = _parse_uuid(business_id)
    if target_uuid is None:
        return []
    result = await session.execute(
        select(Tool).where(
            Tool.business_id == target_uuid,
            Tool.is_active == True,
        )
    )
    return list(result.scalars().all())

async def upsert_system_prompt(business_id: str, prompt_text: str, session: AsyncSession) -> Prompt:
    target_uuid = _parse_uuid(business_id)
    result = await session.execute(select(Prompt).where(Prompt.business_id == target_uuid))
    db_prompt = result.scalar_one_or_none()
    
    if db_prompt:
        db_prompt.system_prompt_template = prompt_text
    else:
        db_prompt = Prompt(business_id=target_uuid, system_prompt_template=prompt_text)
        session.add(db_prompt)
        
    await session.commit()
    await session.refresh(db_prompt)
    return db_prompt

async def upsert_guardrail_config(business_id: str, guardrail_data: dict, session: AsyncSession) -> Guardrail:
    target_uuid = _parse_uuid(business_id)
    result = await session.execute(select(Guardrail).where(Guardrail.business_id == target_uuid))
    db_guardrail = result.scalar_one_or_none()
    
    if db_guardrail:
        for key, value in guardrail_data.items():
            setattr(db_guardrail, key, value)
    else:
        db_guardrail = Guardrail(business_id=target_uuid, **guardrail_data)
        session.add(db_guardrail)
        
    await session.commit()
    await session.refresh(db_guardrail)
    return db_guardrail    