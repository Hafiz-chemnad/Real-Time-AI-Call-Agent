import asyncio
import time
from app.db.session import AsyncSessionLocal
from app.services.business_service import (
    get_system_prompt,
    get_guardrail_config,
    get_business_knowledge,
    get_business_tools,
)

# In-memory dictionary to store the cache: { business_id: (data_dict, timestamp) }
_BUSINESS_CACHE = {}
CACHE_TTL_SECONDS = 300  # Cache lasts for 5 minutes (300 seconds)


async def get_full_business_context(business_id: str) -> dict:
    """
    Fetches the complete configuration for a business by running all four
    lookups concurrently. Uses an in-memory TTL cache to drop subsequent 
    lookup times from 5+ seconds down to 0.001s, preventing Pipecat 
    websocket timeouts during active voice calls.
    """
    current_time = time.time()
    
    # 1. Check if we have fresh data in the cache
    if business_id in _BUSINESS_CACHE:
        cached_data, timestamp = _BUSINESS_CACHE[business_id]
        if current_time - timestamp < CACHE_TTL_SECONDS:
            return cached_data

    # 2. If not in cache (or expired), fetch from DB concurrently
    async def _prompt():
        async with AsyncSessionLocal() as session:
            return await get_system_prompt(business_id, session)

    async def _guardrails():
        async with AsyncSessionLocal() as session:
            return await get_guardrail_config(business_id, session)

    async def _knowledge():
        async with AsyncSessionLocal() as session:
            return await get_business_knowledge(business_id, session)

    async def _tools():
        async with AsyncSessionLocal() as session:
            return await get_business_tools(business_id, session)

    prompt, guardrails, knowledge, tools = await asyncio.gather(
        _prompt(), _guardrails(), _knowledge(), _tools()
    )

    result = {
        "system_prompt": prompt,
        "guardrails": guardrails,
        "knowledge": knowledge,
        "tools": tools,
    }
    
    # 3. Save to cache before returning
    _BUSINESS_CACHE[business_id] = (result, current_time)
    
    return result

def invalidate_business_cache(business_id: str):
    """Busts the local TTL cache when settings change via the dashboard."""
    if business_id in _BUSINESS_CACHE:
        del _BUSINESS_CACHE[business_id]    