"""Custom exception types for agent error handling and recovery."""

class AgentBaseException(Exception):
    """Base exception for all agent runtime errors."""
    def __init__(self, message: str = "An unexpected error occurred."):
        super().__init__(message)
        self.message = message


class ToolExecutionError(AgentBaseException):
    """Raised when an external tool (API or Webhook) fails to execute."""
    def __init__(self, tool_name: str, reason: str = "Unknown error"):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Tool '{tool_name}' failed to execute: {reason}")


class LowConfidenceSTTError(AgentBaseException):
    """Raised when STT confidence falls below the reliability threshold."""
    def __init__(self, transcript: str, confidence: float):
        self.transcript = transcript
        self.confidence = confidence
        super().__init__(f"Low confidence ({confidence:.2f}) for transcript: '{transcript}'")


class LLMGatewayError(AgentBaseException):
    """Raised when all LLM providers in LiteLLM router fail."""
    def __init__(self, detail: str = "All LLM tiers failed"):
        super().__init__(detail)


class BusinessNotFoundError(AgentBaseException):
    """Raised when a business configuration cannot be found in the database."""
    def __init__(self, business_id: str):
        super().__init__(f"Business ID '{business_id}' not found.")