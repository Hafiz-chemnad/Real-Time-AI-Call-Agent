def get_model_for_task(task_type: str) -> str:
    """
    Smart routing rule: decides which model handles a given task type.
    """
    routing_map = {
        "classification": "fast-model",     # Groq — quick intent/routing decisions
        "conversation": "main-model",        # Claude — main reasoning/dialogue
        "fallback": "fallback-model",        # Gemini — used automatically on failure
    }
    return routing_map.get(task_type, "main-model")