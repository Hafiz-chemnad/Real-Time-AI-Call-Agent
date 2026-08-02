import asyncio
from app.brain.intent_classifier import classify_intent

print(asyncio.run(classify_intent("Can I come in tomorrow at 3?")))
print(asyncio.run(classify_intent("What time do you close on Sundays?")))