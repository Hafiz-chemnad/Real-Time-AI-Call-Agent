import asyncio
from app.brain.orchestrator import process_turn

async def run_regression():
    dental_id = "11111111-1111-1111-1111-111111111111"
    law_id = "22222222-2222-2222-2222-222222222222"

    print("\n" + "="*50)
    print("TEST 1: Persona & Knowledge Isolation")
    print("="*50)
    q1 = "What are your hours and pricing?"
    
    # Dental test
    dental_res = await process_turn(q1, business_id=dental_id)
    print(f"🦷 Dental AI ({dental_id}):\n   {dental_res['response']}")
    
    print("-" * 50)
    
    # Law test
    law_res = await process_turn(q1, business_id=law_id)
    print(f"⚖️ Law Firm AI ({law_id}):\n   {law_res['response']}")


    print("\n" + "="*50)
    print("TEST 2: Guardrail Scope Isolation")
    print("="*50)
    q2 = "Can you help me fix my broken car engine?"
    
    # Dental Guardrail test
    dental_scope = await process_turn(q2, business_id=dental_id)
    print(f"🦷 Dental Guardrail:\n   {dental_scope['response']}")
    
    print("-" * 50)
    
    # Law Guardrail test
    law_scope = await process_turn(q2, business_id=law_id)
    print(f"⚖️ Law Firm Guardrail:\n   {law_scope['response']}")


    print("\n" + "="*50)
    print("TEST 3: Dynamic Tool Isolation")
    print("="*50)
    q3_dental = "Book a teeth whitening for 3 PM."
    q3_law = "Schedule a consultation for John Doe regarding a contract dispute."
    
    dental_tool = await process_turn(q3_dental, business_id=dental_id)
    print(f"🦷 Dental Tool Selected: {dental_tool['session_state'].get('pending_booking', {}).get('_tool_name')}")
    
    # Notice the Law tool is set to auto-execute (requires_confirmation=false in SQL)
    law_tool = await process_turn(q3_law, business_id=law_id)
    print(f"⚖️ Law Tool Executed: {law_tool.get('tool_called', {}).get('tool')}")
    print(f"⚖️ Law AI Response: {law_tool['response']}")

if __name__ == "__main__":
    asyncio.run(run_regression())