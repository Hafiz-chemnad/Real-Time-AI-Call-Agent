import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.brain.orchestrator import process_turn

async def main():
    print("🤖 Text-Only Orchestrator Test Started!")
    print("Type 'exit' or 'quit' to stop.")
    print("-" * 60)
    
    session_state = {}
    
    # NOTE: If your DB requires a real business UUID to load tools/system prompts, 
    # replace this with a real one from your `businesses` table.
    test_business_id = "11111111-1111-1111-1111-111111111111" 

    while True:
        try:
            user_input = input("\n🧑 You: ")
            if user_input.strip().lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue

            result = await process_turn(
                transcript=user_input, 
                session_state=session_state, 
                business_id=test_business_id
            )

            # Update session state for the next turn
            session_state = result.get("session_state", {})
            
            # Print the AI's response
            print(f"\n🤖 AI: {result.get('response')}")
            
            # Print debug info so you can see the brain working
            lang = session_state.get('call_language', 'en')
            debug_info = f"   [Lang: {lang}]"
            
            if result.get("language_switch_requested"):
                debug_info += f" [🔄 SWITCH TRIGGERED TO: {result['language_switch_requested']}]"
            if result.get("tool_called"):
                debug_info += f" [🛠️ Tool Executed: {result['tool_called'].get('status', 'success')}]"
            if session_state.get("pending_tool_call"):
                tool_name = session_state['pending_tool_call'].get('_tool_name', 'unknown')
                debug_info += f" [⏳ Pending Confirmation: {tool_name}]"
                
            print(debug_info)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())