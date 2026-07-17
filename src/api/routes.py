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

@router.post("/admin/prompt")
def update_prompt(request: AdminPrompt):
    with open("src/brain/prompts.py", "w", encoding="utf-8") as f:
        # പുതിയ പ്രോംപ്റ്റ് കോഡ് ആയി തന്നെ സേവ് ചെയ്യുന്നു
        f.write(f'SYSTEM_PROMPT = """{request.prompt_text}"""\n')
    return {"message": "Prompt updated successfully"}

# --- 3. Admin Endpoint: Update Data (പുതിയത്) ---
@router.post("/admin/data")
def update_data(request: AdminData):
    try:
        json.loads(request.json_data) # യൂസർ തന്നത് ശരിയായ JSON ആണോ എന്ന് നോക്കുന്നു
        with open("data/faq_data.json", "w", encoding="utf-8") as f:
            f.write(request.json_data)
        return {"message": "Data updated successfully"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")    