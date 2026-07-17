from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_message: str


class ChatResponse(BaseModel):
    bot_response: str

class AdminPrompt(BaseModel):
    prompt_text: str

class AdminData(BaseModel):
    json_data: str    