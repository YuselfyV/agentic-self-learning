from __future__ import annotations

import json
import math
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from agentic_self_learning.schemas import Document, RetrievalResult


TOKEN_PATTERN = re.compile(r"[A-Za-zÀ-ÿ0-9]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


class LocalRetrievalTool:
    """Small local replacement for the original project's retrieve tool."""

    name = "retrieve"
    action_start = "<tool_call>"
    action_end = "</tool_call>"
    response_start = "<tool_response>"
    response_end = "</tool_response>"

    def __init__(self, knowledge_base_path: str | Path):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.documents = self._load_documents(self.knowledge_base_path)
        self.document_tokens = {
            document.id: Counter(tokenize(self._searchable_text(document))) for document in self.documents
        }

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievalResult]:
        query_tokens = Counter(tokenize(query))
        scored = [
            RetrievalResult(document=document, score=self._score(query_tokens, self.document_tokens[document.id]))
            for document in self.documents
        ]
        return [result for result in sorted(scored, key=lambda item: item.score, reverse=True)[:top_k] if result.score > 0]

    def execute_tool_call(self, action_string: str) -> list[RetrievalResult]:
        payload = self._extract_json_between_tags(action_string)
        if payload.get("name") != self.name:
            raise ValueError(f"Unsupported tool call: {payload.get('name')}")
        arguments = payload.get("arguments", {})
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Tool call requires arguments.query as a non-empty string")
        return self.retrieve(query=query, top_k=int(arguments.get("size", 3)))

    def format_tool_response(self, results: list[RetrievalResult]) -> str:
        lines = [self.response_start]
        for result in results:
            lines.append(f"id: {result.document.id}")
            lines.append(f"score: {result.score:.3f}")
            lines.append(f"content: {result.document.contents}")
        lines.append(self.response_end)
        return "\n".join(lines)

    @staticmethod
    def _searchable_text(document: Document) -> str:
        metadata_text = " ".join(document.metadata.values())
        return f"{document.contents} {metadata_text}"

    @staticmethod
    def _load_documents(path: Path) -> list[Document]:
        if not path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {path}")

        documents: list[Document] = []
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                documents.append(
                    Document(
                        id=str(row.get("id", line_number)),
                        contents=str(row["contents"]),
                        metadata={str(k): str(v) for k, v in row.get("metadata", {}).items()},
                    )
                )
        return documents

    @staticmethod
    def _score(query_tokens: Counter[str], document_tokens: Counter[str]) -> float:
        if not query_tokens or not document_tokens:
            return 0.0

        overlap = set(query_tokens) & set(document_tokens)
        if not overlap:
            return 0.0

        dot = sum(query_tokens[token] * document_tokens[token] for token in overlap)
        query_norm = math.sqrt(sum(value * value for value in query_tokens.values()))
        doc_norm = math.sqrt(sum(value * value for value in document_tokens.values()))
        return dot / (query_norm * doc_norm)

    def _extract_json_between_tags(self, text: str) -> dict:
        pattern = re.escape(self.action_start) + r"(.*?)" + re.escape(self.action_end)
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            raise ValueError("No <tool_call> block found")
        return json.loads(match.group(1).strip())


class WikipediaRetrievalTool:
    """Online retrieve tool backed by the public MediaWiki API."""

    name = "retrieve"
    action_start = "<tool_call>"
    action_end = "</tool_call>"
    response_start = "<tool_response>"
    response_end = "</tool_response>"

    def __init__(self, language: str = "en", user_agent: str = "agentic-self-learning-lite/0.1"):
        self.language = language
        self.api_url = f"https://{language}.wikipedia.org/w/api.php"
        self.user_agent = user_agent

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievalResult]:
        pages = self._search_pages(query, top_k)
        if not pages:
            return []
        extracts = self._fetch_extracts([page["pageid"] for page in pages])
        results: list[RetrievalResult] = []
        for index, page in enumerate(pages):
            pageid = str(page["pageid"])
            extract = extracts.get(pageid, "")
            if not extract:
                continue
            title = str(page["title"])
            url_title = urllib.parse.quote(title.replace(" ", "_"))
            results.append(
                RetrievalResult(
                    document=Document(
                        id=f"wikipedia:{pageid}",
                        contents=extract,
                        metadata={
                            "title": title,
                            "url": f"https://{self.language}.wikipedia.org/wiki/{url_title}",
                            "source": "wikipedia",
                        },
                    ),
                    score=float(top_k - index),
                )
            )
        return results

    def execute_tool_call(self, action_string: str) -> list[RetrievalResult]:
        payload = self._extract_json_between_tags(action_string)
        if payload.get("name") != self.name:
            raise ValueError(f"Unsupported tool call: {payload.get('name')}")
        arguments = payload.get("arguments", {})
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Tool call requires arguments.query as a non-empty string")
        return self.retrieve(query=query, top_k=int(arguments.get("size", 3)))

    def format_tool_response(self, results: list[RetrievalResult]) -> str:
        lines = [self.response_start]
        for result in results:
            lines.append(f"id: {result.document.id}")
            lines.append(f"title: {result.document.metadata.get('title', '')}")
            lines.append(f"url: {result.document.metadata.get('url', '')}")
            lines.append(f"content: {result.document.contents}")
        lines.append(self.response_end)
        return "\n".join(lines)

    def _search_pages(self, query: str, limit: int) -> list[dict]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": str(limit),
            "format": "json",
            "utf8": "1",
        }
        data = self._get(params)
        return list(data.get("query", {}).get("search", []))

    def _fetch_extracts(self, pageids: list[int]) -> dict[str, str]:
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": "1",
            "explaintext": "1",
            "pageids": "|".join(str(pageid) for pageid in pageids),
            "format": "json",
            "utf8": "1",
        }
        data = self._get(params)
        pages = data.get("query", {}).get("pages", {})
        return {str(pageid): str(page.get("extract", "")).strip() for pageid, page in pages.items()}

    def _get(self, params: dict[str, str]) -> dict:
        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    def _extract_json_between_tags(self, text: str) -> dict:
        pattern = re.escape(self.action_start) + r"(.*?)" + re.escape(self.action_end)
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            raise ValueError("No <tool_call> block found")
        return json.loads(match.group(1).strip())
