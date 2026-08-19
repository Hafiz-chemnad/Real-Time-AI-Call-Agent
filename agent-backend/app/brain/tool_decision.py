import json
import logging
import re
from typing import Any

from app.brain.router import get_model_for_task

logger = logging.getLogger(__name__)


def _build_tool_schema(tool) -> dict[str, Any]:
    """Converts a DB Tool row into an OpenAI/LiteLLM-style function schema."""
    return {
        "type": "function",
        "function": {
            "name": tool.tool_name,
            "description": tool.description,
            "parameters": tool.parameters,  # stored as JSONB, already schema-shaped
        },
    }


async def _call_llm(**kwargs: Any) -> tuple[Any, str]:
    from app.brain.gateway import call_llm
    return await call_llm(**kwargs)


async def decide_tool_call(
    transcript: str, business_tools: list, chat_history: list | None = None
) -> dict[str, Any] | None:
    if not isinstance(transcript, str) or not transcript.strip():
        return None
    if not business_tools:
        return None

    tool_schemas = [_build_tool_schema(t) for t in business_tools]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a receptionist deciding whether the caller's message "
                "requires calling one of the available tools. Only call a tool "
                "if the caller's request clearly matches it and you have enough "
                "information to fill ALL its required parameters. "
                "CRITICAL: If ANY required parameter is missing, DO NOT call the tool. "
                "Do NOT invent placeholders like 'please specify' or 'unknown'. "
                "Just return a normal text response."
            ),
        },
    ]
    if chat_history:
        messages.extend(chat_history[-4:])
    messages.append({"role": "user", "content": transcript})

    try:
        response, _ = await _call_llm(
            model_name=get_model_for_task("classification"),
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto",
            temperature=0,
        )
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            return None
            
        call = tool_calls[0]
        arguments = json.loads(call.function.arguments)
        
        # PYTHON SAFETY NET: Reject hallucinated placeholders
        matching_tool = next((t for t in business_tools if t.tool_name == call.function.name), None)
        if matching_tool and isinstance(matching_tool.parameters, dict):
            required_fields = matching_tool.parameters.get("required", [])
            for field in required_fields:
                val = arguments.get(field)
                # If it's missing, empty, or contains placeholder text, abort the tool call
                if not val or "specify" in str(val).lower() or "unknown" in str(val).lower():
                    logger.info(f"Missing required slot '{field}'. Letting standard response ask for it.")
                    return None
                    
        return {"tool": call.function.name, "arguments": arguments}
    except Exception:
        logger.exception("decide_tool_call: LLM tool-calling failed")
        return None

async def decide_correction(transcript: str, pending_arguments: dict, business_tools: list) -> dict[str, Any] | None:
    """
    Given a caller's correction (e.g. "actually make it Wednesday at 4")
    and the currently pending tool arguments, asks the LLM to merge the
    correction into the existing arguments — using the same dynamic tool
    schemas as decide_tool_call, not a hardcoded booking assumption.
    """
    if not isinstance(transcript, str) or not transcript.strip():
        return None
    if not business_tools:
        return None

    tool_schemas = [_build_tool_schema(t) for t in business_tools]

    # Figure out which tool this pending booking belongs to, so we can
    # remind the LLM specifically what fields it's editing.
    tool_name = pending_arguments.get("_tool_name")
    matching_tool = next((t for t in business_tools if t.tool_name == tool_name), None)

    try:
        response, _ = await _call_llm(
            model_name=get_model_for_task("classification"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "The caller previously requested this action, with these "
                        f"current details: {json.dumps(pending_arguments)}. "
                        "They are now correcting ONE OR MORE details. Call the same "
                        "tool again with the corrected arguments, keeping every "
                        "field that wasn't mentioned in the correction unchanged."
                    ),
                },
                {"role": "user", "content": transcript},
            ],
            tools=tool_schemas,
            tool_choice={"type": "function", "function": {"name": tool_name}} if matching_tool else "auto",
            temperature=0,
        )

        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            return None

        call = tool_calls[0]
        arguments = json.loads(call.function.arguments)
        arguments["_tool_name"] = call.function.name
        return {"tool": call.function.name, "arguments": arguments}

    except Exception:
        logger.exception("decide_correction: LLM correction merge failed")
        return None        