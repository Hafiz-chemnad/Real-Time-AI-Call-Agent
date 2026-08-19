import asyncio
from app.services.business_service import get_system_prompt
from app.brain.orchestrator import process_turn

async def test_prompts():
    dental_id = "11111111-1111-1111-1111-111111111111"
    law_id = "22222222-2222-2222-2222-222222222222"

    print("=== 1. Testing Direct DB Fetch ===")
    dental_prompt = await get_system_prompt(dental_id)
    law_prompt = await get_system_prompt(law_id)
    
    print(f"[Dental Prompt from DB]: {dental_prompt}")
    print(f"[Law Prompt from DB]:    {law_prompt}\n")

    print("=== 2. Testing AI Brain Responses ===")
    user_question = "Are you open today?"

    print(f"\nCaller: '{user_question}' (Calling Dental Clinic)")
    dental_reply = await process_turn(transcript=user_question, business_id=dental_id)
    print(f"AI: {dental_reply}\n")

    print(f"Caller: '{user_question}' (Calling Law Firm)")
    law_reply = await process_turn(transcript=user_question, business_id=law_id)
    print(f"AI: {law_reply}\n")

if __name__ == "__main__":
    asyncio.run(test_prompts())