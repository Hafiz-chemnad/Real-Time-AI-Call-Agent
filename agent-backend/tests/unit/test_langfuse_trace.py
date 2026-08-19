from dotenv import load_dotenv
load_dotenv()

from app.observability.langfuse_tracer import trace_turn

trace_turn(
    transcript="Are you open today?",
    response="Yep, open till 6!",
    intent="faq_question",
    escalation=None,
    tool_called=None
)
print("Trace sent — check your Langfuse dashboard.")