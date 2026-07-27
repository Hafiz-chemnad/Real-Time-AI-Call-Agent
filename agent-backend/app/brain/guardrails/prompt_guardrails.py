BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "system prompt",
    "reveal prompt",
    "act as",
    "pretend to be",
    "forget previous",
    "jailbreak",
]


class PromptGuardrails:
    """
    Basic prompt injection detector.
    """

    def validate(self, message: str):

        text = message.lower().strip()

        for pattern in BLOCKED_PATTERNS:

            if pattern in text:

                return {
                    "safe": False,
                    "reason": "Prompt Injection",
                    "matched_pattern": pattern,
                }

        return {
            "safe": True,
            "reason": None,
            "matched_pattern": None,
        }


_guardrails = PromptGuardrails()


def validate_prompt(message: str):
    return _guardrails.validate(message)