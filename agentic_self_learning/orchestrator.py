from __future__ import annotations

from pathlib import Path

from agentic_self_learning.agents import AnswerAgent, QuestionAgent, QuestionEvaluatorAgent
from agentic_self_learning.schemas import PipelineResult
from agentic_self_learning.tools import LocalRetrievalTool, WikipediaRetrievalTool


DEFAULT_KNOWLEDGE_BASE = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.jsonl"


class SelfLearningPipeline:
    def __init__(
        self,
        knowledge_base_path: str | Path = DEFAULT_KNOWLEDGE_BASE,
        source: str = "local",
        wikipedia_language: str = "en",
    ):
        retrieval_tool = self._build_retrieval_tool(knowledge_base_path, source, wikipedia_language)
        self.question_agent = QuestionAgent(retrieval_tool)
        self.answer_agent = AnswerAgent(retrieval_tool)
        self.evaluator_agent = QuestionEvaluatorAgent()

    def run(self, topic: str) -> PipelineResult:
        generated_question = self.question_agent.generate(topic)
        answer = self.answer_agent.answer(generated_question.question)
        evaluation = self.evaluator_agent.evaluate(generated_question, answer)
        return PipelineResult(generated_question, answer, evaluation)

    def answer_existing_question(self, question: str) -> PipelineResult:
        answer = self.answer_agent.answer(f"<question>{question}</question>")
        generated_question = self.question_agent.from_existing_question(question, answer)
        evaluation = self.evaluator_agent.evaluate(generated_question, answer)
        return PipelineResult(generated_question, answer, evaluation)

    @staticmethod
    def _build_retrieval_tool(
        knowledge_base_path: str | Path,
        source: str,
        wikipedia_language: str,
    ):
        if source == "local":
            return LocalRetrievalTool(knowledge_base_path)
        if source == "wikipedia":
            return WikipediaRetrievalTool(language=wikipedia_language)
        raise ValueError("source must be 'local' or 'wikipedia'")
