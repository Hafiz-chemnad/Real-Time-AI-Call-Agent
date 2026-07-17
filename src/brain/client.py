from groq import Groq
from src.brain.prompts import SYSTEM_PROMPT
from src.config.settings import settings

# Initialize Groq client
client = Groq(api_key=settings.groq_api_key)

def ask_ai_model(query: str, context: str) -> str:
    user_payload = f"FAQ Context:\n{context}\n\nUser Question: {query}" if context else f"User Question: {query}"

    response = client.chat.completions.create(
        model=settings.model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_payload}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()