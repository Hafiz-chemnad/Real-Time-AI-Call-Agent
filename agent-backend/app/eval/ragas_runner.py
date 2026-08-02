import os
import json
import time
import asyncio
import time
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig

from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
)

from app.brain.orchestrator import process_turn
from app.brain.orchestrator import SAMPLE_KNOWLEDGE

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from app.core.config import settings
from langfuse.callback import CallbackHandler

os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY

DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "test_datasets",
    "faq_dataset.json"
)

def load_eval_questions():
    with open(DATASET_PATH, "r") as f:
        return json.load(f)

# Custom subclass to safely intercept and strip Ragas' injected 'temperature' kwarg,
# and throttle every call ragas makes internally (not just dataset generation) —
# Gemini's free tier caps at 15 requests/min, and ragas fires many sub-calls per
# question (Faithfulness alone splits an answer into statements, then verifies
# each one — easily 5-10+ calls per single question).
class SafeGeminiChat(ChatGoogleGenerativeAI):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        kwargs.pop("temperature", None)
        time.sleep(4.5)  # ~13 calls/min, safely under the 15/min cap
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        kwargs.pop("temperature", None)
        await asyncio.sleep(4.5)
        return await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)

async def generate_eval_dataset():
    data = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": []
    }

    eval_questions = load_eval_questions()

    for item in eval_questions:
        result = await process_turn(item["question"])

        data["question"].append(item["question"])
        data["answer"].append(result["response"])
        data["contexts"].append(SAMPLE_KNOWLEDGE)
        data["ground_truth"].append(item["ground_truth"])

        # Throttling to respect free-tier rate limits
        await asyncio.sleep(5)

    return Dataset.from_dict(data)

async def run_evaluation():
    print("Generating responses for evaluation dataset...")
    eval_dataset = await generate_eval_dataset()
    langfuse_handler = CallbackHandler()
    print("Initializing Gemini and Local Embeddings for Ragas evaluation...")
    gemini_llm = SafeGeminiChat(model="gemini-3.5-flash-lite")

    # Use a lightweight local embedding model to avoid API 404/429 errors entirely
    local_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    ragas_llm = LangchainLLMWrapper(gemini_llm)
    ragas_emb = LangchainEmbeddingsWrapper(local_embeddings)

    print("Running Ragas evaluation metrics...")

    # max_workers=1 avoids concurrent calls; the real throttle now lives inside
    # SafeGeminiChat itself, since ragas fires many sequential sub-calls per
    # question regardless of worker count.
    result = evaluate(
        eval_dataset,
        metrics=[
            ContextPrecision(),
            ContextRecall(),
            Faithfulness(),
            AnswerRelevancy(),
        ],
        callbacks=[langfuse_handler],
        llm=ragas_llm,
        embeddings=ragas_emb,
        run_config=RunConfig(max_workers=1, timeout=180),
        
    )
    time.sleep(2)

    print("\n--- Evaluation Results ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(run_evaluation())