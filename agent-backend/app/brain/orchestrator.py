# app/brain/orchestrator.py

import json
import re
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

from app.core.language import is_malayalam_text

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


async def _reply_from_tool_result(
    system_prompt: str,
    chat_history: list,
    transcript: str,
    tool_name: str,
    tool_result: dict,
    fallback: str,
) -> str:
    """Second LLM pass: turns a tool's raw result into the actual reply.

    Without this, a successful tool call produced only a canned "Done!"
    line and the data the tool returned (a menu, an order id and total, a
    "location pin still needed" flag) never reached the customer. If this
    pass fails for any reason, the caller's canned `fallback` is used, so a
    flaky LLM call can never turn a successful tool call into an error.
    """
    try:
        data = tool_result.get("response", tool_result) if isinstance(tool_result, dict) else tool_result
        payload = json.dumps(data, default=str, ensure_ascii=False)[:6000]

        messages = [{"role": "system", "content": system_prompt}]
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": transcript})
        messages.append({
            "role": "user",
            "content": (
                f"[TOOL RESULT from '{tool_name}' — system data, not written by the customer]\n"
                f"{payload}\n\n"
                "Using ONLY the data above, write your reply to the customer now. "
                "Include the actual details they need: for a menu, every item with its price, one per line; "
                "for a placed order, the order id and total. "
                "If the data shows a step the customer still has to do (for example sharing their location pin), "
                "tell them clearly. Plain text only — no markdown, asterisks or bullet symbols. "
                "Never invent items, prices or details that are not in the data. Do not call any tools."
            ),
        })
        response, _ = await call_llm(model_name="fast-model", messages=messages, temperature=0.3)
        text = (response.choices[0].message.content or "").strip()
        return text or fallback
    except Exception:
        logger.exception("Tool-result reply generation failed; using canned reply")
        return fallback


_ORDER_CLAIM_RE = re.compile(
    r"(order\s*(id|number|no\.?)\s*[:#]?\s*\S*\d{5,})|"
    r"(order\s+(is|has been|was|got)\s+(now\s+)?(confirmed|placed|received))|"
    r"((i(\'ve| have)|we(\'ve| have))\s+(placed|confirmed)\s+your\s+order)|"
    r"(order\s+(confirmed|placed))",
    re.IGNORECASE,
)


def _claims_order_placed(text: str) -> bool:
    return bool(text and _ORDER_CLAIM_RE.search(text))


async def process_turn(
    transcript: str,
    session_state: Optional[dict] = None,
    business_id: str = "11111111-1111-1111-1111-111111111111",
    compose_from_tool_result: bool = False,
) -> dict:
    """Processes one caller turn end-to-end with low-latency single-pass LLM reasoning.

    compose_from_tool_result: when True, after a tool runs successfully the reply
    is written by a second LLM pass from the tool's actual data (a menu, an order
    id/total, ...). Default False keeps the original instant canned confirmations,
    which is what live phone calls want (no extra latency mid-conversation). Text
    channels such as WhatsApp chat pass True because the customer needs the data.
    """

    _t_ctx = _timed("get_full_business_context")
    context = await get_full_business_context(business_id)
    _t_ctx()

    system_prompt = _build_system_prompt(context)
    business_tools = context.get("tools", [])
    custom_escalations = context.get("guardrails").escalate_on if context.get("guardrails") else None

    session_state = session_state or {}
    pending_tool_call = session_state.get("pending_tool_call")
    chat_history = session_state.get("chat_history", [])

    # Turn-1 Language Lock
    if not chat_history and "call_language" not in session_state:
        session_state["call_language"] = "ml" if is_malayalam_text(transcript) else "en"
    
    call_language = session_state.get("call_language", "en")

    call_language = session_state.get("call_language", "en")

    if call_language == "ml":
        system_prompt += (
            "\n\n[CRITICAL LANGUAGE RULE]: You are a Malayalam AI assistant. You MUST strictly reply in Malayalam. "
            "Under absolutely NO circumstances should you generate responses in Hindi, Bengali, Gujarati, or any other language, "
            "even if the user transcript appears to be in those languages. Ignore unintelligible text. "
            "Do NOT use English unless citing a specific brand name."
        )
    else:
        system_prompt += (
            "\n\n[CRITICAL LANGUAGE RULE]: You are an English AI assistant. You MUST strictly reply in English. "
            "Under absolutely NO circumstances should you generate responses in Hindi, Bengali, Gujarati, or any other language, "
            "even if the user transcript appears to be in those languages. Ignore unintelligible text."
        )

    result = {
        "transcript": transcript,
        "intent": None,
        "escalation": None,
        "tool_called": None,
        "response": None,
        "session_state": {},
    }

    # Text ordering chats need to remember the whole order-taking conversation
    # (items, quantities, delivery/pickup, location) — a 4-message window made
    # the AI forget the cart by the time the location pin arrived. Phone calls
    # keep the original short window for latency.
    _keep = 24 if compose_from_tool_result else 6
    _use = 14 if compose_from_tool_result else 4

    def _updated_history(user_msg: str, ai_msg: str) -> list:
        return (chat_history + [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": ai_msg},
        ])[-_keep:]

    def _save_state(**kwargs):
        session_state.update(kwargs)
        result["session_state"] = session_state

    # Bilingual Prompt Injection Handling
    # Bilingual Prompt Injection Handling
    guardrail_check = validate_prompt(transcript)
    if not guardrail_check["safe"]:
        result["escalation"] = "prompt_injection"
        if call_language == "ml":
            result["response"] = "ക്ഷമിക്കണം, ബിസിനസ്സ് സംബന്ധമായ കാര്യങ്ങൾക്കും ബുക്കിംഗുകൾക്കും മാത്രമേ എനിക്ക് സഹായിക്കാൻ കഴിയൂ."
        else:
            result["response"] = "I can only help with business inquiries, scheduling, and standard questions."
        
        # FIX 1: Save state so it doesn't wipe memory on prompt injection
        _save_state(chat_history=_updated_history(transcript, result["response"]))
        _safe_trace(**result)
        return result

    # Bilingual Escalation Handling
    escalation_category = await check_escalation(transcript, custom_escalations, chat_history)
    # The off-topic classifier is meant for phone receptionists. In an ordering
    # chat it misfires on item names and short answers (e.g. an item literally
    # called "hahah"); the system prompt already keeps the AI on topic.
    if compose_from_tool_result and escalation_category == "off_topic":
        escalation_category = "none"
    if escalation_category != "none":
        result["escalation"] = escalation_category
        eng_response = get_escalation_response(escalation_category)
        
        if call_language == "ml":
            if escalation_category == "human_request":
                result["response"] = "തീർച്ചയായും, ഞാൻ നിങ്ങളെ ഒരു കസ്റ്റമർ കെയർ എക്സിക്യൂട്ടീവിന് കണക്ട് ചെയ്യാം."
            elif escalation_category == "frustration":
                result["response"] = "ക്ഷമിക്കണം, ഉണ്ടായ അസൗകര്യത്തിൽ ഞാൻ മാപ്പ് ചോദിക്കുന്നു. ഞാൻ നിങ്ങളെ ഒരു പ്രതിനിധിക്ക് കണക്ട് ചെയ്യാം."
            elif escalation_category == "off_topic":
                # FIX 2: Correct translation so it stops saying it's transferring you!
                result["response"] = "ക്ഷമിക്കണം, എനിക്ക് ക്ലിനിക്കിന്റെ സേവനങ്ങൾക്കും ബുക്കിംഗുകൾക്കും മാത്രമേ സഹായിക്കാൻ കഴിയൂ."
            else:
                result["response"] = "ക്ഷമിക്കണം, എനിക്ക് ഇതിൽ സഹായിക്കാൻ കഴിയില്ല. ഞാൻ നിങ്ങളെ ഒരു പ്രതിനിധിക്ക് കണക്ട് ചെയ്യാം."
        else:
            result["response"] = eng_response
            
        # FIX 3: Save state so it doesn't wipe memory when STT hallucinates off_topic noise
        _save_state(chat_history=_updated_history(transcript, result["response"]))
        _safe_trace(**result)
        return result

    # 3-Tier Confirmation Handling
    if pending_tool_call:
        reply_type = await classify_confirmation_reply(transcript, call_language=call_language)

        if reply_type == "confirmed":
            tool_name = pending_tool_call.get("_tool_name")
            _t_exec = _timed("execute_tool (confirmed)")
            
            try:
                tool_result = await execute_tool(tool_name, pending_tool_call, business_tools)
                _t_exec()
                
                if isinstance(tool_result, dict) and tool_result.get("status") == "error":
                    result["tool_called"] = tool_result
                    if call_language == "ml":
                        result["response"] = (
                            "ക്ഷമിക്കണം, സിസ്റ്റവുമായി ബന്ധിപ്പിക്കുന്നതിൽ ഒരു ചെറിയ തകരാർ ഉണ്ട്. "
                            "നിങ്ങളുടെ വിവരങ്ങൾ ഞാൻ രേഖപ്പെടുത്തിയിട്ടുണ്ട്, ഒരാൾ നിങ്ങളെ തിരികെ വിളിക്കുന്നതാണ്."
                        )
                    else:
                        result["response"] = (
                            "I'm having a little trouble connecting to our system right now. "
                            "I have noted your request and will have a team member follow up with you to confirm."
                        )
                else:
                    result["tool_called"] = tool_result
                    if call_language == "ml":
                        canned = "ശരി, എല്ലാം തയ്യാറാണ്! നിങ്ങളുടെ ബുക്കിംഗ് വിജയകരമായി പൂർത്തിയായി."
                    else:
                        canned = f"Great, you're all set! I have processed your request for {tool_name.replace('_', ' ')}."
                    result["response"] = canned
                    if compose_from_tool_result:
                        result["response"] = await _reply_from_tool_result(
                            system_prompt, chat_history, transcript, tool_name, tool_result, canned
                        )
            except Exception as e:
                _t_exec()
                logger.error(f"Tool execution exception: {e}")
                if call_language == "ml":
                    result["response"] = "ക്ഷമിക്കണം, സിസ്റ്റവുമായി ബന്ധിപ്പിക്കുന്നതിൽ ഒരു ചെറിയ തകരാർ ഉണ്ട്. ഒരാൾ നിങ്ങളെ ഉടൻ തിരികെ വിളിക്കുന്നതാണ്."
                else:
                    result["response"] = "I'm having a little trouble connecting to our system right now. Let me have someone follow up with you."

            _save_state(chat_history=_updated_history(transcript, result["response"]), pending_tool_call=None)
            _safe_trace(**result)
            return result

        if reply_type == "rejected":
            if call_language == "ml":
                result["response"] = "ശരി കുഴപ്പമില്ല. വേറെ എന്തെങ്കിലും സഹായം ആവശ്യമുണ്ടോ?"
            else:
                result["response"] = "No problem. Let me know if you would like help with anything else."
            _save_state(chat_history=_updated_history(transcript, result["response"]), pending_tool_call=None)
            _safe_trace(**result)
            return result

        if reply_type == "correction":
            _t_corr = _timed("decide_correction")
            merged = await decide_correction(transcript, pending_tool_call, business_tools)
            _t_corr()
            if merged:
                updated = merged["arguments"]
                if call_language == "ml":
                    result["response"] = f"ശരി. പുതിയ വിവരങ്ങൾ ഇതാണ് — {_format_args(updated)}. ഞാൻ മുന്നോട്ട് പോകട്ടേ?"
                else:
                    result["response"] = f"Got it. The updated details are — {_format_args(updated)}. Shall I proceed with this?"
                _save_state(pending_tool_call=updated, chat_history=_updated_history(transcript, result["response"]))
                _safe_trace(**result)
                return result
                
            if call_language == "ml":
                result["response"] = "ക്ഷമിക്കണം, ഇതിൽ എന്താണ് മാറ്റേണ്ടത്?"
            else:
                result["response"] = "Sorry, what would you like to change it to?"
            _save_state(chat_history=_updated_history(transcript, result["response"]))
            _safe_trace(**result)
            return result

        # Ambiguous fallback
        if call_language == "ml":
            result["response"] = f"ക്ഷമിക്കണം, എനിക്ക് വ്യക്തമായില്ല. {_format_args(pending_tool_call)} ഉപയോഗിച്ച് ഞാൻ മുന്നോട്ട് പോകട്ടേ?"
        else:
            result["response"] = f"Just to confirm, shall I proceed with {_format_args(pending_tool_call)}?"
            
        _save_state(chat_history=_updated_history(transcript, result["response"]))
        _safe_trace(**result)
        return result

    db_knowledge = context.get("knowledge")
    if db_knowledge:
        knowledge_text = await get_context(transcript, [db_knowledge], business_id=business_id)
        if knowledge_text:
            system_prompt += f"\n\n--- BUSINESS KNOWLEDGE ---\n{knowledge_text}"

    tool_schemas = [_build_tool_schema(t) for t in business_tools] if business_tools else []
    
    tool_schemas.append({
        "type": "function",
        "function": {
            "name": "set_call_language",
            "description": "Call this ONLY when the user explicitly asks to switch the spoken language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {"type": "string", "enum": ["en", "ml"]}
                },
                "required": ["language"]
            }
        }
    })

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-_use:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": transcript})

    _t_llm = _timed("single_pass_llm")
    llm_kwargs = {
        "model_name": "fast-model", 
        "messages": messages,
        "temperature": 0.3,
        "tools": tool_schemas,
        "tool_choice": "auto"
    }

    response, _ = await call_llm(**llm_kwargs)
    _t_llm()

    choice = response.choices[0].message
    tool_calls = getattr(choice, "tool_calls", None)

    if tool_calls:
        call = tool_calls[0]
        tool_name = call.function.name
        try:
            call_args = json.loads(call.function.arguments)
        except Exception:
            call_args = {}

        call_args["_tool_name"] = tool_name

        if tool_name == "set_call_language":
            new_lang = call_args.get("language", "en")
            result["language_switch_requested"] = new_lang
            result["response"] = "ശരി, ഞാൻ ഇനി മലയാളത്തിൽ സംസാരിക്കാം." if new_lang == "ml" else "Sure, I will speak in English now."
            _save_state(chat_history=_updated_history(transcript, result["response"]), call_language=new_lang)
            _safe_trace(**result)
            return result

        matching_tool = next((t for t in business_tools if t.tool_name == tool_name), None)
        # The model cannot know the caller's phone number; the channel does.
        # When it supplies one in session_state, always use that (never trust
        # an LLM-invented value).
        _cust = session_state.get("customer_number")
        if _cust and matching_tool and isinstance(matching_tool.parameters, dict):
            if "customerNumber" in (matching_tool.parameters.get("properties") or {}):
                call_args["customerNumber"] = str(_cust)

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
                if call_language == "ml":
                    result["response"] = (
                        f"ഉറപ്പുവരുത്താൻ വേണ്ടി, {_format_args(call_args)} ഉപയോഗിച്ച് "
                        f"ഈ ബുക്കിംഗ് മുന്നോട്ട് കൊണ്ടുപോകട്ടേ?"
                    )
                else:
                    result["response"] = (
                        f"Just to confirm, you would like me to proceed with {tool_name.replace('_', ' ')} "
                        f"using these details — {_format_args(call_args)}. Is that correct?"
                    )
                
                _save_state(pending_tool_call=call_args, chat_history=_updated_history(transcript, result["response"]))
                _safe_trace(**result)
                return result
            else:
                _t_exec = _timed("execute_tool (auto)")
                try:
                    tool_result = await execute_tool(tool_name, call_args, business_tools)
                    _t_exec()
                    
                    if isinstance(tool_result, dict) and tool_result.get("status") == "error":
                        result["tool_called"] = tool_result
                        if call_language == "ml":
                            result["response"] = "ക്ഷമിക്കണം, ഇത് പൂർത്തിയാക്കുന്നതിൽ ഒരു സാങ്കേതിക തകരാർ ഉണ്ട്. ഒരാൾ നിങ്ങളെ നേരിട്ട് വിളിക്കുന്നതാണ്."
                        else:
                            result["response"] = (
                                "I ran into a technical hiccup trying to process that automatically. "
                                "Let me have someone follow up with you directly."
                            )
                    else:
                        result["tool_called"] = tool_result
                        if call_language == "ml":
                            canned = "ശരി! നിങ്ങളുടെ ബുക്കിംഗ് വിജയകരമായി പൂർത്തിയായി."
                        else:
                            canned = f"Done! I have successfully processed your request for {tool_name.replace('_', ' ')}."
                        result["response"] = canned
                        if compose_from_tool_result:
                            result["response"] = await _reply_from_tool_result(
                                system_prompt, chat_history, transcript, tool_name, tool_result, canned
                            )
                except Exception as e:
                    _t_exec()
                    logger.error(f"Tool execution exception: {e}")
                    if call_language == "ml":
                        result["response"] = "ക്ഷമിക്കണം, ഇത് പൂർത്തിയാക്കുന്നതിൽ ഒരു സാങ്കേതിക തകരാർ ഉണ്ട്. ഒരാൾ നിങ്ങളെ നേരിട്ട് വിളിക്കുന്നതാണ്."
                    else:
                        result["response"] = "I ran into a technical hiccup trying to process that automatically. Let me have someone follow up with you directly."

                _save_state(chat_history=_updated_history(transcript, result["response"]))
                _safe_trace(**result)
                return result

    reply_content = choice.content or "How can I help you today?"

    # Anti-fabrication (chat channels only): no tool ran this turn, so the
    # model must not claim an order was placed / give an order id or total.
    if compose_from_tool_result and _claims_order_placed(reply_content):
        logger.warning("Blocked fabricated order confirmation: %r", reply_content[:200])
        try:
            retry_messages = messages + [
                {"role": "assistant", "content": reply_content},
                {"role": "system", "content": (
                    "Your previous reply claimed an order was placed, but no order was created. "
                    "Orders exist only after the place_order tool returns an order id. Do NOT state "
                    "an order id or total. Either call place_order now (if you have all details) or "
                    "ask the customer for whatever is still missing.")},
            ]
            retry_resp, _ = await call_llm(**{**llm_kwargs, "messages": retry_messages})
            rchoice = retry_resp.choices[0].message
            if getattr(rchoice, "tool_calls", None) or _claims_order_placed(rchoice.content or ""):
                reply_content = "Just to be sure — could you please confirm your order details (items, and delivery or pickup) so I can place it?"
            else:
                reply_content = rchoice.content or reply_content
        except Exception:
            reply_content = "Just to be sure — could you please confirm your order details (items, and delivery or pickup) so I can place it?"

    result["response"] = reply_content.strip()
    _save_state(chat_history=_updated_history(transcript, result["response"]))
    _safe_trace(**result)
    return result