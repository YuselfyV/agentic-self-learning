from __future__ import annotations

import json
import re

from agentic_self_learning.schemas import Answer
from agentic_self_learning.tools import LocalRetrievalTool


class AnswerAgent:
    """Answers a question by calling the retrieve tool."""

    def __init__(self, retrieval_tool: LocalRetrievalTool):
        self.retrieval_tool = retrieval_tool

    def answer(self, question: str) -> Answer:
        clean_question = self._strip_tag(question, "question")
        payload = {"name": "retrieve", "arguments": {"query": clean_question, "size": 3}}
        tool_call = f"<tool_call>{json.dumps(payload, ensure_ascii=False)}</tool_call>"
        evidence = self.retrieval_tool.execute_tool_call(tool_call)
        answer = self._answer_from_evidence(clean_question, evidence)
        return Answer(question=clean_question, answer=f"<answer>{answer}</answer>", evidence=evidence)

    @staticmethod
    def _answer_from_evidence(question: str, evidence) -> str:
        if not evidence:
            return "No answer found"

        pattern_answer = AnswerAgent._answer_by_question_pattern(question, evidence)
        if pattern_answer:
            return pattern_answer

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
    def _answer_by_question_pattern(question: str, evidence) -> str:
        question_lower = question.lower()
        if "capital" not in question_lower:
            return ""

        country = AnswerAgent._extract_capital_target(question)
        for item in evidence:
            title = item.document.metadata.get("title", "")
            contents = item.document.contents
            if title and country and title.lower() != country.lower():
                title_pattern = re.escape(title)
                country_pattern = re.escape(country)
                if re.search(rf"{title_pattern}.*?es la capital.*?{country_pattern}", contents, re.IGNORECASE | re.DOTALL):
                    return title
                if re.search(rf"{title_pattern}.*?is the capital.*?{country_pattern}", contents, re.IGNORECASE | re.DOTALL):
                    return title
            match = re.search(r"(?:distrito capital|capital),\s*([A-ZÁÉÍÓÚÑ][A-Za-zÀ-ÿ]+)", contents)
            if match and country and country.lower() in contents.lower():
                return match.group(1)
        return ""

    @staticmethod
    def _extract_capital_target(question: str) -> str:
        patterns = [
            r"capital\s+de\s+(.+?)(?:\?|$)",
            r"capital\s+of\s+(.+?)(?:\?|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1).strip(" .¿?¡!")
        return ""

    @staticmethod
    def _strip_tag(text: str, tag: str) -> str:
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
        return match.group(1).strip() if match else text.strip()
