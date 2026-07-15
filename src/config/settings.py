from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # AI Configuration (Groq)
    groq_api_key: str
    model_name: str = "llama-3.1-8b-instant"
    
    # App Configuration
    app_env: str = "development"
    port: int = 8000

    # ഇത് പൈത്തണിനോട് .env ഫയലിൽ നിന്ന് ഡാറ്റ വായിക്കാൻ പറയുന്നു
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# ഈ 'settings' എന്ന വേരിയബിൾ വഴിയാണ് ബാക്കി എല്ലാ ഫയലുകളും API Key എടുക്കുന്നത്
settings = Settings()