from __future__ import annotations

import re

from agentic_self_learning.schemas import Answer, Evaluation, GeneratedQuestion
from agentic_self_learning.tools.retrieval import tokenize


class QuestionEvaluatorAgent:
    """Evaluates whether the generated question is solvable and the answer matches."""

    def evaluate(self, generated_question: GeneratedQuestion, answer: Answer) -> Evaluation:
        expected = self._strip_tag(generated_question.expected_answer, "answer")
        predicted = self._strip_tag(answer.answer, "answer")
        question = self._strip_tag(generated_question.question, "question")
        question_is_solvable = bool(generated_question.evidence and expected and question)

        if not question_is_solvable:
            return Evaluation(
                conclusion="uncertain",
                score=0.0,
                reason="La pregunta no tiene evidencia suficiente o no tiene formato interrogativo.",
                question_is_solvable=False,
            )

        matches = self._normalize(expected) == self._normalize(predicted)
        return Evaluation(
            conclusion="correct" if matches else "wrong",
            score=1.0 if matches else 0.0,
            reason=(
                "La respuesta coincide con la respuesta esperada."
                if matches
                else f"La respuesta esperada era '{expected}', pero el agente respondio '{predicted}'."
            ),
            question_is_solvable=True,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(tokenize(text))

    @staticmethod
    def _strip_tag(text: str, tag: str) -> str:
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
        return match.group(1).strip() if match else text.strip()
