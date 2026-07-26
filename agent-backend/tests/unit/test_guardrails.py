# tests/unit/test_guardrails.py
import asyncio

# ---------------------------------------------------------
# Person B fills in: hallucination guardrail test cases
# (questions NOT covered by the sample knowledge base)
# ---------------------------------------------------------
HALLUCINATION_TEST_CASES = [
    # "Is there free parking outside?",
]

# ---------------------------------------------------------
# Person C fills in: escalation guardrail test cases
# (transcript, expected_escalation_type)
# ---------------------------------------------------------
ESCALATION_TEST_CASES = [
    # ("This is the third time I've called, just get me a real person!", "human_request"),
]


async def run_hallucination_tests():
    if not HALLUCINATION_TEST_CASES:
        print("No hallucination test cases yet — Person B needs to fill these in")
        return
    from app.knowledge.vectorless import answer_faq  # adjust import once B builds this
    for question in HALLUCINATION_TEST_CASES:
        answer = await answer_faq(question)
        print(f"Q: {question}\nA: {answer}\n")


async def run_escalation_tests():
    if not ESCALATION_TEST_CASES:
        print("No escalation test cases yet — Person C needs to fill these in")
        return
    from app.brain.guardrails.escalation import check_escalation, get_escalation_response
    for transcript, expected in ESCALATION_TEST_CASES:
        result = await check_escalation(transcript)
        response = get_escalation_response(result)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status} — expected {expected}, got {result} — \"{transcript}\"\n  → {response}\n")


async def run_all():
    await run_hallucination_tests()
    await run_escalation_tests()


if __name__ == "__main__":
    asyncio.run(run_all())