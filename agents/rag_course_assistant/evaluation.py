"""Lightweight answer evaluation helpers for classroom RAG exercises."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .vector_store import RetrievedChunk


INSUFFICIENT_EVIDENCE_MARKERS = (
    "no tengo evidencia suficiente",
    "no hay evidencia suficiente",
    "el contexto no contiene",
    "no se encuentra en los documentos",
)


@dataclass(frozen=True)
class EvaluationResult:
    """Simple rubric result for a RAG answer."""

    relevance: str
    grounding: str
    source_use: str
    risk_notes: list[str]

    @property
    def passed(self) -> bool:
        """Return whether the answer satisfies the minimum classroom rubric."""

        return (
            self.relevance == "ok"
            and self.grounding == "ok"
            and self.source_use == "ok"
            and not self.risk_notes
        )


def evaluate_answer(
    question: str,
    answer: str,
    retrieved_chunks: list[RetrievedChunk],
) -> EvaluationResult:
    """Evaluate a RAG answer with transparent heuristics for class discussion."""

    normalized_answer = answer.lower()
    normalized_question = question.lower()
    risk_notes: list[str] = []

    relevance = "ok" if _has_token_overlap(normalized_question, normalized_answer) else "review"

    if retrieved_chunks:
        chunk_ids = {chunk.chunk_id for chunk in retrieved_chunks if chunk.chunk_id}
        cited_ids = set(re.findall(r"chunk_\d{3}", normalized_answer))
        source_use = "ok" if cited_ids & chunk_ids else "review"
        grounding = "ok" if _answer_mentions_retrieved_terms(answer, retrieved_chunks) else "review"
    else:
        source_use = "ok" if _has_insufficient_evidence_marker(normalized_answer) else "review"
        grounding = source_use

    if source_use == "review":
        risk_notes.append("La respuesta no cita claramente los chunks recuperados.")
    if grounding == "review":
        risk_notes.append("La respuesta no parece apoyarse en terminos del contexto recuperado.")
    if not retrieved_chunks and not _has_insufficient_evidence_marker(normalized_answer):
        risk_notes.append("No habia contexto recuperado y la respuesta no reconoce la limitacion.")

    return EvaluationResult(
        relevance=relevance,
        grounding=grounding,
        source_use=source_use,
        risk_notes=risk_notes,
    )


def _has_insufficient_evidence_marker(answer: str) -> bool:
    return any(marker in answer for marker in INSUFFICIENT_EVIDENCE_MARKERS)


def _has_token_overlap(question: str, answer: str) -> bool:
    question_terms = _meaningful_terms(question)
    answer_terms = _meaningful_terms(answer)
    if not question_terms:
        return bool(answer.strip())
    return bool(question_terms & answer_terms)


def _answer_mentions_retrieved_terms(
    answer: str,
    retrieved_chunks: list[RetrievedChunk],
) -> bool:
    answer_terms = _meaningful_terms(answer.lower())
    context_terms: set[str] = set()
    for chunk in retrieved_chunks:
        context_terms.update(_meaningful_terms(chunk.text.lower()))
    return len(answer_terms & context_terms) >= 3


def _meaningful_terms(text: str) -> set[str]:
    stopwords = {
        "para",
        "como",
        "con",
        "del",
        "las",
        "los",
        "que",
        "una",
        "por",
        "segun",
        "sobre",
        "esta",
        "este",
        "son",
        "sus",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9áéíóúñü]+", text.lower())
        if len(token) > 3 and token not in stopwords
    }
