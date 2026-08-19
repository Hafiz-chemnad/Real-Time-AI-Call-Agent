import asyncio
from app.brain.orchestrator import process_turn

async def test_dynamic_tools():
    dental_id = "11111111-1111-1111-1111-111111111111"

    print("\n" + "="*50)
    print("=== TURN 1: The Caller Requests an Action ===")
    print("="*50)
    req_1 = "I need to book a teeth whitening appointment for Friday at 3 PM."
    print(f"📞 Caller: {req_1}")
    
    # Run turn 1
    result_1 = await process_turn(req_1, business_id=dental_id)
    print(f"🦷 AI: {result_1['response']}")
    
    # Check if it dynamically grabbed the tool name from Postgres!
    pending = result_1['session_state'].get('pending_booking', {})
    print(f"🔧 LLM Selected Tool: {pending.get('_tool_name')}")


    print("\n" + "="*50)
    print("=== TURN 2: The Caller Confirms ===")
    print("="*50)
    req_2 = "Yes, that is correct!"
    print(f"📞 Caller: {req_2}")
    
    # Run turn 2, PASSING BACK the session state from turn 1
    result_2 = await process_turn(req_2, session_state=result_1['session_state'], business_id=dental_id)
    print(f"🦷 AI: {result_2['response']}")
    
    print("\n📡 --- API EXECUTION RESULT --- 📡")
    tool_exec = result_2.get('tool_called', {})
    print(f"Status: {tool_exec.get('status')} ({tool_exec.get('status_code')})")
    print(f"Tool:   {tool_exec.get('tool')}")
    if tool_exec.get('status') == 'success':
        # httpbin echoes our payload back under the 'json' key
        echoed_data = tool_exec.get('response', {}).get('json')
        print(f"Payload Sent to API: {echoed_data}")

if __name__ == "__main__":
    asyncio.run(test_dynamic_tools())