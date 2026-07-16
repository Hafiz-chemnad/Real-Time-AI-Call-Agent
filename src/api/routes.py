from fastapi import APIRouter
from src.api.schemas import ChatRequest, ChatResponse
from src.memory.retriever import retrieve_faq_context
from src.brain.client import ask_ai_model

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    context = retrieve_faq_context(request.user_message)
    
    ai_response = ask_ai_model(query=request.user_message, context=context)
    
    return ChatResponse(bot_response=ai_response)