from __future__ import annotations

import argparse

from agentic_self_learning.orchestrator import DEFAULT_KNOWLEDGE_BASE, SelfLearningPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Self-Learning Lite")
    parser.add_argument("--topic", default="capitales", help="Tema para generar una pregunta.")
    parser.add_argument("--question", help="Pregunta existente para responder.")
    parser.add_argument("--knowledge-base", default=str(DEFAULT_KNOWLEDGE_BASE), help="Ruta al JSONL de conocimiento.")
    parser.add_argument("--source", choices=["local", "wikipedia"], default="local", help="Fuente de investigacion.")
    parser.add_argument("--wikipedia-language", default="en", help="Idioma de Wikipedia, por ejemplo en o es.")
    args = parser.parse_args()

    pipeline = SelfLearningPipeline(
        args.knowledge_base,
        source=args.source,
        wikipedia_language=args.wikipedia_language,
    )
    result = pipeline.answer_existing_question(args.question) if args.question else pipeline.run(args.topic)

    print("Question Agent")
    print(result.generated_question.question)
    print(result.generated_question.expected_answer)
    print()
    print("Answer Agent")
    print(result.answer.answer)
    print()
    print("Question Evaluator Agent")
    print(f"<answer>conclusion: {result.evaluation.conclusion}</answer>")
    print(f"score: {result.evaluation.score}")
    print(f"reason: {result.evaluation.reason}")


if __name__ == "__main__":
    main()
