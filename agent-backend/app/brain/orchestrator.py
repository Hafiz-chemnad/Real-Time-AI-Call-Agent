# app/brain/orchestrator.py

import json
import logging
import time
from typing import Optional, Any

from app.brain.gateway import call_llm
from app.brain.guardrails.prompt_guardrails import validate_prompt
from app.brain.guardrails.escalation import check_escalation, get_escalation_response
from app.brain.guardrails.confirmation import classify_confirmation_reply
from app.brain.tool_decision import _build_tool_schema, decide_correction
from app.knowledge.selector import get_context
from app.tools.execution.executor import execute_tool
from app.observability.langfuse_tracer import trace_turn
from app.domain.business_config import get_full_business_context

logger = logging.getLogger(__name__)


def _timed(label: str):
    start = time.perf_counter()
    def _end():
        print(f"⏱️  [{label}] {time.perf_counter() - start:.2f}s")
    return _end


def _safe_trace(**kwargs):
    try:
        trace_turn(**kwargs)
    except Exception:
        pass


SYSTEM_PROMPT = (
    "You are a friendly, professional voice receptionist answering a phone call for a business.\n"
    "CRITICAL PHONE RULES:\n"
    "1. Keep responses short and conversational (usually 1-2 concise sentences).\n"
    "2. Ask ONE question or make ONE statement, then STOP and wait for the caller to speak.\n"
    "3. NEVER answer your own questions or predict the caller's next reply.\n"
    "4. No markdown, asterisks, bullet points, or special characters.\n"
)


def _format_args(args_dict: dict) -> str:
    return ", ".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in args_dict.items() if not k.startswith("_")])


def _tool_requires_confirmation(tool_name: str, business_tools: list) -> bool:
    matched_tool = next((t for t in business_tools if t.tool_name == tool_name), None)
    if matched_tool is None:
        return True
    return bool(getattr(matched_tool, "requires_confirmation", True))


def _build_system_prompt(context: dict) -> str:
    db_prompt = context.get("system_prompt", "")
    base = SYSTEM_PROMPT
    if db_prompt and db_prompt.strip():
        base = SYSTEM_PROMPT + f"\n--- BUSINESS INSTRUCTIONS ---\n{db_prompt.strip()}"

    guardrails = context.get("guardrails")
    if guardrails:
        if guardrails.scope:
            base += f"\n[SCOPE]: {guardrails.scope}"
            if guardrails.out_of_scope_response:
                base += f"\nIf asked outside this scope, reply with: '{guardrails.out_of_scope_response}'"
        if guardrails.never_reveal:
            base += f"\n[SECRETS - NEVER REVEAL]: {', '.join(guardrails.never_reveal)}."
        if guardrails.no_hallucination_instruction:
            base += f"\n[ACCURACY]: {guardrails.no_hallucination_instruction}"

    return base


async def process_turn(
    transcript: str,
    session_state: Optional[dict] = None,
    business_id: str = "11111111-1111-1111-1111-111111111111"
) -> dict:
    """Processes one caller turn end-to-end with low-latency single-pass LLM reasoning."""

    # 1. Fetch Business Context
    _t_ctx = _timed("get_full_business_context")
    context = await get_full_business_context(business_id)
    _t_ctx()

    system_prompt = _build_system_prompt(context)
    business_tools = context.get("tools", [])
    custom_escalations = context.get("guardrails").escalate_on if context.get("guardrails") else None

    session_state = session_state or {}
    pending_tool_call = session_state.get("pending_tool_call")
    chat_history = session_state.get("chat_history", [])

    result = {
        "transcript": transcript,
        "intent": None,
        "escalation": None,
        "tool_called": None,
        "response": None,
        "session_state": {},
    }

    def _updated_history(user_msg: str, ai_msg: str) -> list:
        return (chat_history + [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": ai_msg},
        ])[-6:]

    # 2. Instant Prompt Guardrail Check
    guardrail_check = validate_prompt(transcript)
    if not guardrail_check["safe"]:
        result["escalation"] = "prompt_injection"
        result["response"] = "I can only help with business inquiries, scheduling, and standard questions."
        _safe_trace(**result)
        return result

    # 3. Instant Regex Escalation Pre-check
    escalation_category = await check_escalation(transcript, custom_escalations, chat_history)
    if escalation_category != "none":
        result["escalation"] = escalation_category
        result["response"] = get_escalation_response(escalation_category)
        _safe_trace(**result)
        return result

    # 4. Handle Pending Tool Confirmations
    if pending_tool_call:
        reply_type = classify_confirmation_reply(transcript)

        if reply_type == "confirmed":
            tool_name = pending_tool_call.get("_tool_name")
            _t_exec = _timed("execute_tool (confirmed)")
            
            try:
                tool_result = await execute_tool(tool_name, pending_tool_call, business_tools)
                _t_exec()
                
                # ✅ GRACEFUL ERROR HANDLING FOR CONFIRMED TOOLS
                if isinstance(tool_result, dict) and tool_result.get("status") == "error":
                    result["tool_called"] = tool_result
                    result["response"] = (
                        "I'm having a little trouble connecting to our system right now. "
                        "I have noted your request and will have a team member follow up with you to confirm."
                    )
                else:
                    result["tool_called"] = tool_result
                    result["response"] = f"Great, you're all set! I have processed your request for {tool_name.replace('_', ' ')}."
            except Exception as e:
                _t_exec()
                logger.error(f"Tool execution exception: {e}")
                result["response"] = "I'm having a little trouble connecting to our system right now. Let me have someone follow up with you."

            result["session_state"] = {"chat_history": _updated_history(transcript, result["response"])}
            _safe_trace(**result)
            return result

        if reply_type == "rejected":
            result["response"] = "No problem. Let me know if you would like help with anything else."
            result["session_state"] = {"chat_history": _updated_history(transcript, result["response"])}
            _safe_trace(**result)
            return result

        if reply_type == "correction":
            _t_corr = _timed("decide_correction")
            merged = await decide_correction(transcript, pending_tool_call, business_tools)
            _t_corr()
            if merged:
                updated = merged["arguments"]
                result["response"] = f"Got it. The updated details are — {_format_args(updated)}. Shall I proceed with this?"
                result["session_state"] = {
                    "pending_tool_call": updated,
                    "chat_history": _updated_history(transcript, result["response"]),
                }
                _safe_trace(**result)
                return result
            result["response"] = "Sorry, what would you like to change it to?"
            result["session_state"] = {
                "pending_tool_call": pending_tool_call,
                "chat_history": _updated_history(transcript, result["response"]),
            }
            _safe_trace(**result)
            return result

        result["response"] = f"Just to confirm, shall I proceed with {_format_args(pending_tool_call)}?"
        result["session_state"] = {
            "pending_tool_call": pending_tool_call,
            "chat_history": _updated_history(transcript, result["response"]),
        }
        _safe_trace(**result)
        return result

    # 5. Retrieve Context Knowledge (FAQ / Business Info)
    db_knowledge = context.get("knowledge")
    if db_knowledge:
        knowledge_text = await get_context(transcript, [db_knowledge], business_id=business_id)
        if knowledge_text:
            system_prompt += f"\n\n--- BUSINESS KNOWLEDGE ---\n{knowledge_text}"

    # 6. Single-Pass Execution (Dialogue + Tool Decision in ONE Call)
    tool_schemas = [_build_tool_schema(t) for t in business_tools] if business_tools else None

    # Construct proper multi-turn messages
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-4:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": transcript})

    _t_llm = _timed("single_pass_llm")
    llm_kwargs = {
        "model_name": "fast-model",  # Uses fast Groq Llama-3.3 (300ms)
        "messages": messages,
        "temperature": 0.3,
    }
    if tool_schemas:
        llm_kwargs["tools"] = tool_schemas
        llm_kwargs["tool_choice"] = "auto"

    response, _ = await call_llm(**llm_kwargs)
    _t_llm()

    choice = response.choices[0].message
    tool_calls = getattr(choice, "tool_calls", None)

    # If the LLM triggered a tool:
    if tool_calls:
        call = tool_calls[0]
        tool_name = call.function.name
        try:
            call_args = json.loads(call.function.arguments)
        except Exception:
            call_args = {}

        call_args["_tool_name"] = tool_name

        # Check required fields
        matching_tool = next((t for t in business_tools if t.tool_name == tool_name), None)
        missing_required = False
        if matching_tool and isinstance(matching_tool.parameters, dict):
            required = matching_tool.parameters.get("required", [])
            for req in required:
                val = str(call_args.get(req, "")).lower()
                if not val or "specify" in val or "unknown" in val:
                    missing_required = True
                    break

        if not missing_required:
            if _tool_requires_confirmation(tool_name, business_tools):
                result["response"] = (
                    f"Just to confirm, you would like me to proceed with {tool_name.replace('_', ' ')} "
                    f"using these details — {_format_args(call_args)}. Is that correct?"
                )
                result["session_state"] = {
                    "pending_tool_call": call_args,
                    "chat_history": _updated_history(transcript, result["response"]),
                }
                _safe_trace(**result)
                return result
            else:
                _t_exec = _timed("execute_tool (auto)")
                try:
                    tool_result = await execute_tool(tool_name, call_args, business_tools)
                    _t_exec()
                    
                    # ✅ GRACEFUL ERROR HANDLING FOR AUTO TOOLS
                    if isinstance(tool_result, dict) and tool_result.get("status") == "error":
                        result["tool_called"] = tool_result
                        result["response"] = (
                            "I ran into a technical hiccup trying to process that automatically. "
                            "Let me have someone follow up with you directly."
                        )
                    else:
                        result["tool_called"] = tool_result
                        result["response"] = f"Done! I have successfully processed your request for {tool_name.replace('_', ' ')}."
                except Exception as e:
                    _t_exec()
                    logger.error(f"Tool execution exception: {e}")
                    result["response"] = "I ran into a technical hiccup trying to process that automatically. Let me have someone follow up with you directly."

                result["session_state"] = {"chat_history": _updated_history(transcript, result["response"])}
                _safe_trace(**result)
                return result

    # Regular conversational response
    reply_content = choice.content or "How can I help you today?"
    result["response"] = reply_content.strip()
    result["session_state"] = {"chat_history": _updated_history(transcript, result["response"])}
    _safe_trace(**result)
    return result