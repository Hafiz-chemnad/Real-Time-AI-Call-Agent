import litellm
from litellm import Router
from app.core.config import settings

# Enable LiteLLM's built-in caching (in-memory for now — Redis later in production)
litellm.cache = litellm.Cache(type="local")

# Model list — maps a friendly name to the actual provider/model + credentials
# Model list — maps a friendly name to the actual provider/model + credentials
# Model list — maps a friendly name to the actual provider/model + credentials
# Model list — maps a friendly name to the actual provider/model + credentials
model_list = [
    {
        "model_name": "fast-model",
        "litellm_params": {"model": "groq/openai/gpt-oss-120b", "api_key": settings.GROQ_API_KEY}, # ✅ Official 70B replacement
    },
    {
        "model_name": "main-model",
        "litellm_params": {"model": "gemini/gemini-3.5-flash-lite", "api_key": settings.GEMINI_API_KEY},
    },
    {
        "model_name": "fallback-model",
        "litellm_params": {"model": "groq/openai/gpt-oss-20b", "api_key": settings.GROQ_API_KEY}, # ✅ Official 8B replacement
    },
]

router = Router(
    model_list=model_list,
    fallbacks=[
        {"fast-model": ["fallback-model"]},
        {"main-model": ["fallback-model"]},
    ],
    num_retries=2,
)
async def call_llm(model_name: str, messages: list, **kwargs):
    response = await router.acompletion(
        model=model_name,
        messages=messages,
        caching=True,
        **kwargs,
    )
    actual_model = response.model  # the model that actually generated this response
    return response, actual_model