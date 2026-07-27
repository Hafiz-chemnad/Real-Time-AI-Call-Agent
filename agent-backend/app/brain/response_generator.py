from typing import List, Dict, Optional

from app.brain.gateway import call_llm


class ResponseGenerator:
    """
    Generates responses using the configured LLM.
    """

    def __init__(self):
        pass

    def build_system_prompt(
        self,
        base_prompt: str,
        knowledge: Optional[str] = None,
    ) -> str:

        prompt = base_prompt.strip()

        if knowledge:
            prompt += f"\n\nBusiness Knowledge:\n{knowledge}"

        return prompt

    def build_messages(
        self,
        system_prompt: str,
        history: Optional[List[Dict]],
        user_message: str,
    ) -> List[Dict]:

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        if history:
            messages.extend(history)

        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        return messages

    async def generate_response(
        self,
        user_message: str,
        base_prompt: str,
        knowledge: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        model_name: str = "main-model",
    ) -> str:

        system_prompt = self.build_system_prompt(
            base_prompt,
            knowledge,
        )

        messages = self.build_messages(
            system_prompt,
            history,
            user_message,
        )

        response, _ = await call_llm(
            model_name=model_name,
            messages=messages,
        )

        return response.choices[0].message.content.strip()


_generator = ResponseGenerator()


async def generate_response(
    user_message: str,
    base_prompt: str,
    knowledge: Optional[str] = None,
    history: Optional[List[Dict]] = None,
    model_name: str = "main-model",
):
    return await _generator.generate_response(
        user_message=user_message,
        base_prompt=base_prompt,
        knowledge=knowledge,
        history=history,
        model_name=model_name,
    )