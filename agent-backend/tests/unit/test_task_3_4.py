import asyncio
from app.brain.orchestrator import process_turn

async def test_knowledge():
    dental_id = "11111111-1111-1111-1111-111111111111"
    law_id = "22222222-2222-2222-2222-222222222222"
    
    print("\n=== TEST 1: The Dental Clinic ===")
    q1 = "What are your business hours and how much is teeth whitening?"
    r1 = await process_turn(transcript=q1, business_id=dental_id)
    print(f"🦷 AI: {r1['response']}")

    print("\n=== TEST 2: The Law Firm ===")
    q2 = "What are your business hours and how much is a consultation?"
    r2 = await process_turn(transcript=q2, business_id=law_id)
    print(f"⚖️ AI: {r2['response']}")

if __name__ == "__main__":
    asyncio.run(test_knowledge())