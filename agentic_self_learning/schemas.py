from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    id: str
    contents: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalResult:
    document: Document
    score: float


@dataclass(frozen=True)
class GeneratedQuestion:
    question: str
    expected_answer: str
    evidence: list[RetrievalResult]


@dataclass(frozen=True)
class Answer:
    question: str
    answer: str
    evidence: list[RetrievalResult]


@dataclass(frozen=True)
class Evaluation:
    conclusion: str
    score: float
    reason: str
    question_is_solvable: bool


@dataclass(frozen=True)
class PipelineResult:
    generated_question: GeneratedQuestion
    answer: Answer
    evaluation: Evaluation
