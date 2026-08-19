import asyncio
from app.brain.orchestrator import process_turn

async def run_memory_test():
    # Real business ID from your database for Smile Dental
    business_id = "11111111-1111-1111-1111-111111111111"
    
    session_state = {
        "chat_history": [],
        "pending_tool_call": None
    }

    # 4-turn gauntlet testing slot extraction, short answers, and confirmation
    turns = [
        "I'd like to book a dental checkup.",
        "Monday",
        "9 AM",
        "Yes, proceed"
    ]

    print("\n" + "=" * 60)
    print("🦷 STARTING STAGE 1 MEMORY & STATE RETENTION TEST")
    print("=" * 60 + "\n")
    
    for i, user_text in enumerate(turns, 1):
        print(f"👤 TURN {i} - CALLER: \"{user_text}\"")
        
        # Call your orchestrator with the exact signature
        result = await process_turn(
            transcript=user_text,
            session_state=session_state,
            business_id=business_id
        )
        
        # Update session state for the next turn
        session_state = result.get("session_state", {})
        
        print(f"🤖 AI RESPONSE: {result.get('response')}")
        print(f"   [Intent]      : {result.get('intent')}")
        print(f"   [Escalation]  : {result.get('escalation')}")
        print(f"   [Tool Called] : {result.get('tool_called')}")
        print(f"   [History Len] : {len(session_state.get('chat_history', []))} messages")
        print(f"   [Pending Tool]: {session_state.get('pending_tool_call')}")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_memory_test())