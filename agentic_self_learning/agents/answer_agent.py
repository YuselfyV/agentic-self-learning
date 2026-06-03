from __future__ import annotations

import re

from agentic_self_learning.schemas import Answer
from agentic_self_learning.tools import LocalRetrievalTool


class AnswerAgent:
    """Answers a question by calling the retrieve tool."""

    def __init__(self, retrieval_tool: LocalRetrievalTool):
        self.retrieval_tool = retrieval_tool

    def answer(self, question: str) -> Answer:
        clean_question = self._strip_tag(question, "question")
        tool_call = (
            "<tool_call>"
            f'{{"name": "retrieve", "arguments": {{"query": "{clean_question}", "size": 3}}}}'
            "</tool_call>"
        )
        evidence = self.retrieval_tool.execute_tool_call(tool_call)
        answer = self._answer_from_evidence(evidence)
        return Answer(question=clean_question, answer=f"<answer>{answer}</answer>", evidence=evidence)

    @staticmethod
    def _answer_from_evidence(evidence) -> str:
        if not evidence:
            return "No answer found"
        metadata_answer = evidence[0].document.metadata.get("answer")
        if metadata_answer:
            return metadata_answer
        contents = evidence[0].document.contents
        title = evidence[0].document.metadata.get("title")
        if title and title.lower() in contents.lower():
            return title
        words = re.findall(r"[A-Z][A-Za-zÀ-ÿ]+(?:\s+[A-Z][A-Za-zÀ-ÿ]+)*", contents)
        return words[-1] if words else contents.split(".")[0].strip()

    @staticmethod
    def _strip_tag(text: str, tag: str) -> str:
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
        return match.group(1).strip() if match else text.strip()
