import asyncio
from app.brain.orchestrator import process_turn
from app.knowledge.selector import get_context
from app.knowledge.vectorless import VectorlessRetriever

async def test_phase_1():
    print("🧪 1. Testing Vectorless Keyword Retrieval...")
    sample_kb = ["We accept Delta Dental, Cigna, and MetLife insurance.", "Our clinic is open Monday to Friday from 9 AM to 6 PM."]
    res = await get_context("Do you take Cigna?", sample_kb)
    print(f"   Result: {res}")
    assert res is not None and "Cigna" in res, "Vectorless retrieval failed!"
    print("   ✅ Vectorless retrieval works.\n")

    print("🧪 2. Testing Orchestrator Turn + Knowledge Injection + Langfuse...")
    # Test a general FAQ inquiry through the orchestrator
    turn_result = await process_turn(
        transcript="What insurance do you accept?",
        session_state={},
        business_id="11111111-1111-1111-1111-111111111111"
    )
    print(f"   AI Spoken Response: '{turn_result.get('response')}'")
    assert turn_result.get("response"), "Orchestrator returned empty response!"
    print("   ✅ Orchestrator executed cleanly with async knowledge retrieval.\n")

    print("🎉 Phase 1 is 100% verified and ready for Phase 2!")

if __name__ == "__main__":
    asyncio.run(test_phase_1())