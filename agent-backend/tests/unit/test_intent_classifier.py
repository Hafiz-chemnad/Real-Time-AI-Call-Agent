# tests/unit/test_intent_classifier.py
import asyncio
from app.brain.intent_classifier import classify_intent
from tests.fixtures.sample_transcripts import SAMPLE_TRANSCRIPTS


async def run_tests():
    if not SAMPLE_TRANSCRIPTS:
        print("No test cases yet — Person B needs to fill in sample_transcripts.py")
        return

    correct = 0
    for case in SAMPLE_TRANSCRIPTS:
        result = await classify_intent(case["transcript"])
        passed = case["expected_intent"] in result
        correct += passed
        status = "PASS" if passed else "FAIL"
        print(f"{status} — expected {case['expected_intent']}, got {result} — \"{case['transcript']}\"")

    print(f"\n{correct}/{len(SAMPLE_TRANSCRIPTS)} correct")


if __name__ == "__main__":
    asyncio.run(run_tests())