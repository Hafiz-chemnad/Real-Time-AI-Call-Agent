# tests/unit/test_tool_executor.py
import asyncio

# Person C fills this in — varied booking phrasings to test tool_decision.py
BOOKING_TEST_CASES = [
    # "Can I get a cleaning appointment next Tuesday at 3?",
]


async def run_tests():
    if not BOOKING_TEST_CASES:
        print("No booking test cases yet — Person C needs to fill these in")
        return
    from app.brain.tool_decision import decide_tool_call
    for transcript in BOOKING_TEST_CASES:
        result = await decide_tool_call(transcript)
        print(f"Transcript: {transcript}\nResult: {result}\n")


if __name__ == "__main__":
    asyncio.run(run_tests())