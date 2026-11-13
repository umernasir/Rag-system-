

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import LLMContextPrecisionWithoutReference
from ragas import SingleTurnSample

load_dotenv()

DATA_FILE = Path("evaluation_data.jsonl")

async def main():
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is missing from .env")

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Evaluation file not found: {DATA_FILE.resolve()}"
        )

    evaluator_model = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
    )

    evaluator_llm = LangchainLLMWrapper(evaluator_model)

    metric = LLMContextPrecisionWithoutReference(
        llm=evaluator_llm
    )

    scores = []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            data = json.loads(line)

            question = data["user_input"]
            contexts = data["retrieved_contexts"]
            response = data["response"]

            if not contexts:
                print(f"Record {line_number}: no contexts; skipped.")
                continue

            sample = SingleTurnSample(
                user_input=question,
                retrieved_contexts=contexts,
                response=response,
            )

            score = await metric.single_turn_ascore(sample)
            scores.append(score)

            print(f"\nRecord: {line_number}")
            print(f"Question: {question}")
            print(f"Retrieved contexts: {len(contexts)}")
            print(f"Context Precision: {score:.4f}")

    if scores:
        average = sum(scores) / len(scores)
        print(f"\nEvaluated records: {len(scores)}")
        print(f"Average Context Precision: {average:.4f}")
    else:
        print("\nNo records were evaluated.")

if __name__ == "__main__":
    asyncio.run(main())