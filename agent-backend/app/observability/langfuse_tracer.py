import os
from langfuse import Langfuse
from typing import Dict, Any, Optional

# Initialize Langfuse client
try:
    langfuse = Langfuse()
except Exception as e:
    langfuse = None
    print(f"Langfuse initialization failed (check API keys): {e}")

def trace_turn(
    transcript: str, 
    response: str, 
    intent: Optional[str] = None, 
    escalation: Optional[str] = None, 
    tool_called: Optional[Dict[str, Any]] = None
):
    """
    Logs a single conversation turn to Langfuse using the standard client interface.
    """
    if not langfuse:
        return

    try:
        # Create a trace for the interaction
        trace = langfuse.trace(
            name="process_turn",
            input=transcript,
            output=response,
            metadata={
                "intent": intent,
                "escalation": escalation,
                "tool_called": tool_called
            }
        )
        
        # Log the specific generation for the LLM response
        trace.generation(
            name="agent_response",
            input=transcript,
            output=response,
            metadata={"intent": intent}
        )
        
        # Force flush to sync immediately with your local dashboard
        langfuse.flush()
    except Exception as ex:
        print(f"Langfuse tracing error: {ex}")