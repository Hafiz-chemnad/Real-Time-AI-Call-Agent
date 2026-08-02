"""
Milestone 1 regression test suite.

Hits the running FastAPI server's /test/process-turn endpoint with a battery
of cases covering Tasks 1.1-1.7, and prints pass/fail counts against each
task's done-check threshold.

Usage:
    1. Start your server (e.g. `uvicorn app.main:app --reload`)
    2. python milestone1_test_suite.py --base-url http://localhost:8000

Notes:
- Booking / confirmation flow cases are multi-turn: the script sends turn 1,
  captures `session_state` from the response, then sends turn 2 with that
  state passed back in (exactly how a real caller session would work).
- Pass/fail judgments for open-ended text responses (KB answers, hallucination
  guardrail, escalation wording) use simple heuristics (keyword presence,
  absence of fabricated details) since there's no ground-truth string match
  for natural language. Read the printed transcript for anything the
  heuristic flags as uncertain.
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

import requests


@dataclass
class CaseResult:
    task: str
    name: str
    passed: bool
    detail: str = ""


RESULTS: list[CaseResult] = []


def call(base_url: str, transcript: str, session_state: Optional[dict] = None) -> dict:
    resp = requests.post(
        f"{base_url}/test/process-turn",
        json={"transcript": transcript, "session_state": session_state or {}},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def record(task: str, name: str, passed: bool, detail: str = ""):
    RESULTS.append(CaseResult(task=task, name=name, passed=passed, detail=detail))
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {task} :: {name}")
    if detail:
        print(f"        {detail}")


# ---------------------------------------------------------------------------
# Task 1.1 — Base system prompt (persona/tone)
# ---------------------------------------------------------------------------
def test_1_1(base_url: str):
    cases = [
        "Are you open today?",
        "Hi there!",
        "Thanks, bye!",
    ]
    for msg in cases:
        r = call(base_url, msg)
        response = (r.get("response") or "")
        # heuristic: short, no markdown headers/bullets, not essay-length
        is_short = len(response.split()) <= 40
        no_markdown = not any(tok in response for tok in ["#", "- ", "* ", "1."])
        passed = is_short and no_markdown
        record(
            "1.1",
            f"persona tone: {msg!r}",
            passed,
            f"response={response!r}",
        )


# ---------------------------------------------------------------------------
# Task 1.2 — Intent classification
# ---------------------------------------------------------------------------
INTENT_CASES = [
    ("Can I come in tomorrow at 3?", "booking"),
    ("What time do you close on Sundays?", "faq_question"),
    ("I've called three times and no one's helped me!", "complaint"),  # or escalation, see note
    ("Cancel my appointment for Friday.", "cancel"),
    ("Can we move my appointment to Thursday instead?", "reschedule"),
    ("I'd like to order a large pepperoni pizza.", "ordering"),
    ("Actually cancel that pizza order.", "order_modification"),
    ("Do you take Cigna insurance?", "faq_question"),
    ("How much does a cleaning cost?", "faq_question"),
    ("Where are you located?", "faq_question"),
    ("Hello!", "greeting"),
    ("Thanks, that's all.", "goodbye"),
    ("What's the capital of France?", "unknown"),
    ("I want to speak to a manager.", "escalation"),
    ("I'm a bit annoyed but I still want to book Tuesday at 3.", "booking"),
]


def test_1_2(base_url: str):
    correct = 0
    for msg, expected in INTENT_CASES:
        r = call(base_url, msg)
        # escalation-type messages get short-circuited before intent
        # classification runs, so "intent" will be None for those —
        # treat that as satisfying an "escalation" expectation.
        intent = r.get("intent")
        escalation = r.get("escalation")
        if expected == "escalation":
            ok = escalation is not None
        elif expected == "complaint" and escalation is not None:
            # frustration phrased as a complaint may legitimately be
            # caught by the escalation guardrail instead — acceptable.
            ok = True
        else:
            ok = intent == expected
        correct += int(ok)
        record(
            "1.2",
            f"intent: {msg!r}",
            ok,
            f"expected={expected} got intent={intent!r} escalation={escalation!r}",
        )
    print(f"\n  Task 1.2 score: {correct}/{len(INTENT_CASES)} (done-check: >=9/10 equivalent)\n")


# ---------------------------------------------------------------------------
# Task 1.3 — Knowledge base retrieval (vectorless)
# ---------------------------------------------------------------------------
KB_CASES = [
    ("Do you take Cigna?", ["cigna"]),
    ("What are your hours on Saturday?", ["10", "2"]),
    ("Are you open Sundays?", ["closed", "sunday"]),
    ("Do you accept Delta Dental?", ["delta dental"]),
    ("How much notice do you need to cancel?", ["24 hour"]),
]


def test_1_3(base_url: str):
    for msg, expect_any in KB_CASES:
        r = call(base_url, msg)
        response = (r.get("response") or "").lower()
        passed = any(kw.lower() in response for kw in expect_any)
        record(
            "1.3",
            f"kb retrieval: {msg!r}",
            passed,
            f"response={r.get('response')!r} (expected one of {expect_any})",
        )


# ---------------------------------------------------------------------------
# Task 1.4 — Hallucination guardrail (question NOT in KB)
# ---------------------------------------------------------------------------
NOT_IN_KB_CASES = [
    "Is there free parking outside?",
    "Do you have a kids' menu?",
    "Can I pay with Bitcoin?",
]

# phrases that would indicate the model fabricated an answer instead of
# admitting uncertainty
FABRICATION_RED_FLAGS = ["yes, we have", "yes we do", "absolutely, we offer"]
UNCERTAINTY_MARKERS = ["not sure", "don't have that", "not totally sure", "follow up", "check on that", "not certain"]


def test_1_4(base_url: str):
    for msg in NOT_IN_KB_CASES:
        r = call(base_url, msg)
        response = (r.get("response") or "").lower()
        no_fabrication = not any(flag in response for flag in FABRICATION_RED_FLAGS)
        shows_uncertainty = any(marker in response for marker in UNCERTAINTY_MARKERS)
        passed = no_fabrication and shows_uncertainty
        record(
            "1.4",
            f"hallucination guardrail: {msg!r}",
            passed,
            f"response={r.get('response')!r}",
        )


# ---------------------------------------------------------------------------
# Task 1.5 — Tool-calling for book_appointment (via full booking flow)
# ---------------------------------------------------------------------------
BOOKING_PHRASINGS = [
    "Can I get a cleaning appointment next Tuesday at 3?",
    "I'd like to book a checkup for tomorrow at 10am.",
    "Schedule me a filling for next Monday at 2pm.",
    "Can I come in for a cleaning on Friday at 9?",
    "Book an appointment for a whitening this Thursday at 4pm.",
    "I need to set up a consultation for next Wednesday at 11am.",
    "Get me in for a checkup next Friday at 1:30pm.",
    "Reserve a cleaning slot for Monday at 3:30.",
]


def test_1_5(base_url: str):
    correct = 0
    for msg in BOOKING_PHRASINGS:
        r = call(base_url, msg)
        state = r.get("session_state") or {}
        pending = state.get("pending_booking")
        has_all_fields = bool(
            pending
            and pending.get("service")
            and pending.get("date")
            and pending.get("time")
        )
        correct += int(has_all_fields)
        record(
            "1.5",
            f"tool-call extraction: {msg!r}",
            has_all_fields,
            f"pending_booking={pending!r}",
        )
    print(f"\n  Task 1.5 score: {correct}/{len(BOOKING_PHRASINGS)} (done-check: >=8/10 equivalent)\n")


# ---------------------------------------------------------------------------
# Task 1.6 — Confirmation-before-action guardrail (multi-turn)
# ---------------------------------------------------------------------------
def test_1_6(base_url: str):
    msg = "Book me a cleaning next Tuesday at 3."
    turn1 = call(base_url, msg)
    state = turn1.get("session_state") or {}
    pending = state.get("pending_booking")

    asked_confirmation = bool(pending) and "?" in (turn1.get("response") or "")
    not_silently_booked = turn1.get("tool_called") is None
    record(
        "1.6",
        "confirmation asked before booking",
        asked_confirmation and not_silently_booked,
        f"turn1_response={turn1.get('response')!r} tool_called={turn1.get('tool_called')!r}",
    )

    if pending:
        turn2 = call(base_url, "Yes, that's right.", session_state=state)
        booked = turn2.get("tool_called") is not None
        record(
            "1.6",
            "booking executes after confirmation",
            booked,
            f"turn2_response={turn2.get('response')!r} tool_called={turn2.get('tool_called')!r}",
        )

        # rejection path
        turn1b = call(base_url, msg)
        state_b = turn1b.get("session_state") or {}
        turn2b = call(base_url, "No, never mind.", session_state=state_b)
        rejected_cleanly = turn2b.get("tool_called") is None
        record(
            "1.6",
            "booking cancelled on rejection",
            rejected_cleanly,
            f"turn2b_response={turn2b.get('response')!r}",
        )


# ---------------------------------------------------------------------------
# Task 1.7 — Escalation / out-of-scope guardrail
# ---------------------------------------------------------------------------
ESCALATION_CASES = [
    ("This is the third time I've called, just get me a real person!", "handoff"),
    ("What's the capital of France?", "redirect"),
    ("I want to speak to a manager right now.", "handoff"),
    ("Can you write me an essay about the French revolution?", "redirect"),
]


def test_1_7(base_url: str):
    for msg, kind in ESCALATION_CASES:
        r = call(base_url, msg)
        escalation = r.get("escalation")
        response = (r.get("response") or "").lower()
        did_not_answer_normally = escalation is not None
        record(
            "1.7",
            f"escalation/out-of-scope: {msg!r}",
            did_not_answer_normally,
            f"escalation={escalation!r} response={r.get('response')!r}",
        )


# ---------------------------------------------------------------------------
# Task 1.10 — Full regression pass (combined edge case)
# ---------------------------------------------------------------------------
def test_1_10(base_url: str):
    r = call(base_url, "I'm a bit annoyed but I still want to book Tuesday at 3.")
    state = r.get("session_state") or {}
    pending = state.get("pending_booking")
    escalated_incorrectly = r.get("escalation") is not None
    still_booked = bool(pending) or r.get("tool_called") is not None
    passed = (not escalated_incorrectly) and still_booked
    record(
        "1.10",
        "frustration + valid booking request not escalated away",
        passed,
        f"escalation={r.get('escalation')!r} pending_booking={pending!r} response={r.get('response')!r}",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    suites: list[tuple[str, Callable[[str], None]]] = [
        ("1.1", test_1_1),
        ("1.2", test_1_2),
        ("1.3", test_1_3),
        ("1.4", test_1_4),
        ("1.5", test_1_5),
        ("1.6", test_1_6),
        ("1.7", test_1_7),
        ("1.10", test_1_10),
    ]

    for name, fn in suites:
        print(f"\n=== Task {name} ===")
        try:
            fn(args.base_url)
        except requests.RequestException as exc:
            print(f"  ERROR calling server: {exc}")
            sys.exit(1)

    print("\n=== Summary ===")
    by_task: dict[str, list[CaseResult]] = {}
    for res in RESULTS:
        by_task.setdefault(res.task, []).append(res)

    total_pass = total = 0
    for task, cases in by_task.items():
        p = sum(c.passed for c in cases)
        t = len(cases)
        total_pass += p
        total += t
        print(f"  Task {task}: {p}/{t} passed")
    print(f"\n  Overall: {total_pass}/{total} passed")

    failures = [c for c in RESULTS if not c.passed]
    if failures:
        print("\n=== Failures (review these) ===")
        for c in failures:
            print(f"  [{c.task}] {c.name}\n      {c.detail}")


if __name__ == "__main__":
    main()
