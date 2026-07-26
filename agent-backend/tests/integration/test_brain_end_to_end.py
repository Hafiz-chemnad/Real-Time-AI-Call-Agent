# tests/integration/test_brain_end_to_end.py
import asyncio

# This is the Milestone 1 "done" checkpoint — runs everything together.
# Fill in real calls once brain/orchestrator.py has been updated with
# Person B's and Person C's finished pieces wired in.

async def run_full_regression():
    print("Running full Milestone 1 regression...\n")

    print("--- Intent classification ---")
    from tests.unit.test_intent_classifier import run_tests as run_intent_tests
    await run_intent_tests()

    print("\n--- Guardrails (hallucination + escalation) ---")
    from tests.unit.test_guardrails import run_all as run_guardrail_tests
    await run_guardrail_tests()

    print("\n--- Tool-calling ---")
    from tests.unit.test_tool_executor import run_tests as run_tool_tests
    await run_tool_tests()

    print("\nAll suites run. Review output above for individual pass/fail.")


if __name__ == "__main__":
    asyncio.run(run_full_regression())