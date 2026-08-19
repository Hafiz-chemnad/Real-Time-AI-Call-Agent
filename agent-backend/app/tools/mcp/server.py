import json
import logging
from typing import Any
from mcp.server import Server
import mcp.types as types

from app.tools.mcp.schema_builder import build_tool_schemas
from app.tools.execution.executor import execute_tool

logger = logging.getLogger(__name__)

# Create the MCP Server instance as defined in your architecture plan
mcp_server = Server("agent-business-tools")

@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    Exposes the business's tools to Claude using the MCP protocol.
    Converts your DB tool schemas into the format Anthropic's MCP expects.
    """
    # Fetches the tool schemas from your schema_builder.py
    schemas = build_tool_schemas()
    
    mcp_tools = []
    for schema in schemas:
        function_data = schema.get("function", {})
        mcp_tools.append(
            types.Tool(
                name=function_data.get("name", "unknown_tool"),
                description=function_data.get("description", ""),
                inputSchema=function_data.get("parameters", {})
            )
        )
    return mcp_tools

@mcp_server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """
    Handles the tool execution request from Claude via MCP.
    Passes the request to your generic tool executor.
    """
    logger.info(f"MCP Server routing tool execution for: {name}")
    args_dict = arguments or {}
    
    try:
        # Executes the API or Webhook via your executor.py
        # Note: In a fully dynamic DB flow, the business_tools list would be injected via session context
        result = await execute_tool(tool_name=name, arguments=args_dict, business_tools=[])
        
        return [
            types.TextContent(
                type="text",
                text=json.dumps(result)
            )
        ]
    except Exception as e:
        logger.error(f"MCP tool execution failed: {e}")
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "error": str(e)})
            )
        ]