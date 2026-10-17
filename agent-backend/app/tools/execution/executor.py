import asyncio
import logging
from typing import Any
import aiohttp

logger = logging.getLogger(__name__)

async def _execute_api_tool(tool, arguments: dict[str, Any], timeout_s: float = 5.0) -> dict[str, Any]:
    """Execute an API-type tool by making the configured HTTP request with a timeout."""
    method = (tool.method or "POST").upper()
    url = tool.url

    body = tool.body_template or arguments

    headers = {}
    if tool.auth_config:
        auth_type = tool.auth_config.get("type")
        if auth_type == "bearer":
            headers["Authorization"] = f"Bearer {tool.auth_config.get('token')}"
        elif auth_type == "api_key":
            headers[tool.auth_config.get("header", "X-API-Key")] = tool.auth_config.get("key")

    # Strict timeout so the AI never freezes (5s by default — what live phone
    # calls need; text chat passes a longer one because the callback server
    # may be a cold/slow free-tier instance).
    timeout = aiohttp.ClientTimeout(total=timeout_s)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method, url, json=body, headers=headers) as resp:
                response_data = await resp.json() if resp.content_type == "application/json" else await resp.text()
                if resp.status >= 400:
                    logger.warning(f"Tool {tool.tool_name} -> HTTP {resp.status}: {str(response_data)[:300]}")
                return {
                    "status": "success" if resp.status < 400 else "error",
                    "status_code": resp.status,
                    "tool": tool.tool_name,
                    "response": response_data,
                }
    except asyncio.TimeoutError:
        logger.warning(f"Tool {tool.tool_name} timed out after {timeout_s} seconds.")
        return {
            "status": "error", 
            "tool": tool.tool_name, 
            "error": "timeout",
            "response": "The system took too long to respond. Inform the user you are having connection issues and will follow up."
        }
    except Exception as e:
        logger.error(f"API Tool error: {e}")
        return {"status": "error", "error": str(e)}


async def _execute_webhook_tool(tool, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a webhook-type tool by POSTing the arguments as-is with a timeout."""
    timeout = aiohttp.ClientTimeout(total=5.0)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(tool.webhook_url, json=arguments) as resp:
                response_data = await resp.json() if resp.content_type == "application/json" else await resp.text()
                return {
                    "status": "success" if resp.status < 400 else "error",
                    "status_code": resp.status,
                    "tool": tool.tool_name,
                    "response": response_data,
                }
    except asyncio.TimeoutError:
        logger.warning(f"Tool {tool.tool_name} timed out after 5 seconds.")
        return {
            "status": "error", 
            "tool": tool.tool_name, 
            "error": "timeout",
            "response": "The system took too long to respond. Inform the user you are having connection issues and will follow up."
        }
    except Exception as e:
        logger.error(f"Webhook Tool error: {e}")
        return {"status": "error", "error": str(e)}


async def execute_tool(tool_name: str, arguments: dict[str, Any], business_tools: list, timeout_s: float = 5.0) -> dict[str, Any]:
    """
    Dynamically executes whichever tool was selected, looked up from the
    business's actual configured tools.
    """
    tool = next((t for t in business_tools if t.tool_name == tool_name), None)
    if tool is None:
        return {"status": "error", "tool": tool_name, "error": "tool_not_found_or_inactive"}

    if tool.execution_type == "api":
        return await _execute_api_tool(tool, arguments, timeout_s)
    elif tool.execution_type == "webhook":
        return await _execute_webhook_tool(tool, arguments)

    return {"status": "error", "tool": tool_name, "error": "unsupported_execution_type"}