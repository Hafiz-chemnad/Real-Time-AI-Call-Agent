import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_target_business
from app.schemas.tool import ToolCreate, ToolResponse
from app.services import tool_service
from app.schemas.tool import ToolUpdate
from app.domain.business_config import invalidate_business_cache

# Notice the dynamic {business_id} in the path to match your multi-tenant architecture
router = APIRouter(prefix="/businesses/{business_id}/tools", tags=["tools"])

@router.get("/", response_model=list[ToolResponse])
async def list_tools(business_id: uuid.UUID = Depends(get_target_business), db: AsyncSession = Depends(get_db)):
    return await tool_service.get_tools_by_business(db, business_id)

@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def add_tool(tool_in: ToolCreate, business_id: uuid.UUID = Depends(get_target_business), db: AsyncSession = Depends(get_db)):
    result = await tool_service.create_tool(db, business_id, tool_in)
    invalidate_business_cache(str(business_id))
    return result

@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tool(
    tool_id: uuid.UUID, 
    business_id: uuid.UUID = Depends(get_target_business), 
    db: AsyncSession = Depends(get_db)
):
    """Deletes a tool."""
    success = await tool_service.delete_tool(db, tool_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")
    invalidate_business_cache(str(business_id))


@router.put("/{tool_id}", response_model=ToolResponse)
async def edit_tool(
    tool_id: uuid.UUID, 
    tool_in: ToolUpdate, 
    business_id: uuid.UUID = Depends(get_target_business), 
    db: AsyncSession = Depends(get_db)
):
    """Updates an existing tool's configuration."""
    updated = await tool_service.update_tool(db, tool_id, tool_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Tool not found")
    invalidate_business_cache(str(business_id))
    return updated