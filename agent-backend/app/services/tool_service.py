import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tool import Tool
from app.schemas.tool import ToolCreate, ToolUpdate

async def create_tool(db: AsyncSession, business_id: uuid.UUID, tool_data: ToolCreate) -> Tool:
    """Creates a new tool for a specific business."""
    db_tool = Tool(**tool_data.model_dump(), business_id=business_id)
    db.add(db_tool)
    await db.commit()
    await db.refresh(db_tool)
    return db_tool

async def get_tools_by_business(db: AsyncSession, business_id: uuid.UUID) -> list[Tool]:
    """Fetches all tools belonging to a business to display on the dashboard."""
    result = await db.execute(select(Tool).where(Tool.business_id == business_id))
    return list(result.scalars().all())

async def update_tool(db: AsyncSession, tool_id: uuid.UUID, tool_data: ToolUpdate) -> Tool | None:
    """Updates an existing tool's configuration."""
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    db_tool = result.scalar_one_or_none()
    
    if not db_tool:
        return None
        
    for key, value in tool_data.model_dump(exclude_unset=True).items():
        setattr(db_tool, key, value)
        
    await db.commit()
    await db.refresh(db_tool)
    return db_tool

async def delete_tool(db: AsyncSession, tool_id: uuid.UUID) -> bool:
    """Deletes a tool from the database."""
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    db_tool = result.scalar_one_or_none()
    
    if not db_tool:
        return False
        
    await db.delete(db_tool)
    await db.commit()
    return True