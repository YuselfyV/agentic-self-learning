from __future__ import annotations

import re

from agentic_self_learning.schemas import GeneratedQuestion
from agentic_self_learning.schemas import Answer
from agentic_self_learning.tools import LocalRetrievalTool


class QuestionAgent:
    """Generates factual questions that can be answered with one concrete entity."""

    def __init__(self, retrieval_tool: LocalRetrievalTool):
        self.retrieval_tool = retrieval_tool

    def generate(self, topic: str) -> GeneratedQuestion:
        evidence = self.retrieval_tool.retrieve(topic, top_k=1)
        if not evidence:
            evidence = [self.retrieval_tool.retrieve(document.contents, top_k=1)[0] for document in self.retrieval_tool.documents[:1]]

        document = evidence[0].document
        question = document.metadata.get("question") or self._question_from_document(document.contents)
        expected_answer = document.metadata.get("answer") or self._answer_from_document(document.contents)

        return GeneratedQuestion(
            question=f"<question>{question}</question>",
            expected_answer=f"<answer>{expected_answer}</answer>",
            evidence=evidence,
        )

    def from_existing_question(self, question: str, answer: Answer) -> GeneratedQuestion:
        expected_answer = self._strip_tag(answer.answer, "answer")
        return GeneratedQuestion(
            question=f"<question>{question}</question>",
            expected_answer=f"<answer>{expected_answer}</answer>",
            evidence=answer.evidence,
        )

    @staticmethod
    def _question_from_document(contents: str) -> str:
        match = re.search(r"(.+?) is (?:the |a |an )?(.+?)\.", contents)
        if match:
            return f"What is {match.group(1).strip()}?"
        return "What concrete entity is described in the evidence?"

    @staticmethod
    def _answer_from_document(contents: str) -> str:
        words = re.findall(r"[A-Z][A-Za-zÀ-ÿ]+(?:\s+[A-Z][A-Za-zÀ-ÿ]+)*", contents)
        return words[-1] if words else contents.split(".")[0].strip()

    @staticmethod
    def _strip_tag(text: str, tag: str) -> str:
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
        return match.group(1).strip() if match else text.strip()
