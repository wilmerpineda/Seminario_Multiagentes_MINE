"""Classroom multi-agent workflow using a local Ollama model.

The example is intentionally small: it shows the architecture of a collaborative
workflow without requiring CrewAI, AutoGen or additional orchestration
dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import ollama

from .prompts import (
    FINAL_WRITER_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    RESEARCHER_SYSTEM_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    WRITER_SYSTEM_PROMPT,
    build_final_writer_prompt,
    build_planner_prompt,
    build_researcher_prompt,
    build_reviewer_prompt,
    build_writer_prompt,
)


DEFAULT_BUSINESS_CASE_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "rag_business_case"
)

FALLBACK_BUSINESS_CASE = {
    "reporte_comercial_q3_2026.md": """
# Reporte Comercial Q3 2026 - NovaRetail

## Resumen ejecutivo

El margen bruto consolidado fue de 34.6%. La reduccion del margen se explica
principalmente por mayores descuentos comerciales en tecnologia y por incremento
en costos logisticos de entregas express.

## Canales de venta

El canal digital represento el 42% de las ventas totales y crecio 14.2% frente
a Q2. El canal de tiendas fisicas mostro menor dinamismo en ciudades intermedias,
con crecimiento de 1.9%. El canal B2B crecio 9.7%, impulsado por contratos con
empresas del sector salud y educacion.

## Recomendaciones del comite

El comite recomienda reducir descuentos generalizados y migrar hacia descuentos
segmentados por rentabilidad. Tambien recomienda crear alertas tempranas para
clientes con entregas tardias recurrentes.
""".strip(),
    "acta_comite_logistica_q3_2026.md": """
# Acta Comite Logistica Q3 2026 - NovaRetail

## Hallazgos principales

Pereira, Bucaramanga y Manizales concentraron el 31% de las incidencias
logisticas. La causa principal fue capacidad limitada de operadores locales en
picos de demanda.

## Riesgos abiertos

El principal riesgo es lanzar campanas digitales agresivas sin resolver la
capacidad logistica. Esto podria aumentar reclamos, costos express y churn.

## Recomendaciones del comite

Antes de ampliar campanas digitales en ciudades intermedias, se recomienda
revisar acuerdos logisticos y coordinar cualquier campana de crecimiento con
operaciones.
""".strip(),
    "politica_descuentos_2026.md": """
# Politica Comercial de Descuentos 2026 - NovaRetail

## Objetivo

La politica de descuentos busca proteger la rentabilidad comercial y evitar
promociones que aumenten ventas sin generar margen suficiente.

## Segmentacion

Los descuentos deben priorizar clientes con alto potencial de recompra, baja
probabilidad de devolucion y margen historico positivo.
""".strip(),
}


class ChatModel(Protocol):
    """Minimal interface needed by the multi-agent workflow."""

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Return model output for a system and user prompt."""


@dataclass(frozen=True)
class LocalOllamaLLM:
    """Small wrapper around the local Ollama chat API."""

    model_name: str = "qwen2.5:3b"
    temperature: float = 0.1

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Call the configured local Ollama model."""

        response: dict[str, Any] = ollama.chat(
            model=self.model_name,
            options={"temperature": self.temperature},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response["message"]["content"]


@dataclass(frozen=True)
class DocumentChunk:
    """Small document chunk used by the classroom retriever."""

    chunk_id: str
    text: str
    source: str
    section: str
    position: int


@dataclass(frozen=True)
class RetrievedEvidence:
    """Evidence chunk selected for the Researcher."""

    chunk_id: str
    source: str
    section: str
    text: str
    score: int

    def to_context_block(self) -> str:
        """Format evidence for a model prompt."""

        return (
            f"[{self.chunk_id}]\n"
            f"Fuente: {Path(self.source).name}\n"
            f"Seccion: {self.section}\n"
            f"Texto: {self.text}"
        )


@dataclass(frozen=True)
class AgentStep:
    """Output produced by one agent role."""

    agent_name: str
    role: str
    content: str


@dataclass(frozen=True)
class MultiAgentResult:
    """Complete result returned by the multi-agent workflow."""

    question: str
    model: str
    retrieved_evidence: list[RetrievedEvidence]
    plan: AgentStep
    research: AgentStep
    draft: AgentStep
    review: AgentStep
    final_answer: AgentStep

    @property
    def steps(self) -> list[AgentStep]:
        """Return agent outputs in execution order."""

        return [self.plan, self.research, self.draft, self.review, self.final_answer]


class ClassroomMultiAgentSystem:
    """Sequential Planner -> Researcher -> Writer -> Reviewer workflow."""

    def __init__(
        self,
        model_name: str = "qwen2.5:3b",
        documents_dir: str | Path = DEFAULT_BUSINESS_CASE_DIR,
        llm: ChatModel | None = None,
        top_k: int = 5,
    ) -> None:
        self.model_name = model_name
        self.documents_dir = Path(documents_dir)
        self.llm = llm or LocalOllamaLLM(model_name=model_name)
        self.top_k = top_k
        self._chunks: list[DocumentChunk] | None = None

    def answer(self, question: str) -> MultiAgentResult:
        """Run the full multi-agent workflow."""

        evidence = self.retrieve_evidence(question)
        evidence_context = "\n\n---\n\n".join(
            item.to_context_block() for item in evidence
        )

        plan_content = self.llm.chat(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=build_planner_prompt(question),
        )
        plan = AgentStep(
            agent_name="Planner",
            role="Coordina el trabajo y define el plan.",
            content=plan_content,
        )

        research_content = self.llm.chat(
            system_prompt=RESEARCHER_SYSTEM_PROMPT,
            user_prompt=build_researcher_prompt(
                question=question,
                plan=plan.content,
                evidence_context=evidence_context,
            ),
        )
        research = AgentStep(
            agent_name="Researcher",
            role="Extrae hallazgos desde evidencia recuperada.",
            content=research_content,
        )

        draft_content = self.llm.chat(
            system_prompt=WRITER_SYSTEM_PROMPT,
            user_prompt=build_writer_prompt(
                question=question,
                plan=plan.content,
                research=research.content,
            ),
        )
        draft = AgentStep(
            agent_name="Writer",
            role="Redacta el borrador ejecutivo.",
            content=draft_content,
        )

        review_content = self.llm.chat(
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            user_prompt=build_reviewer_prompt(
                question=question,
                evidence_context=evidence_context,
                research=research.content,
                draft=draft.content,
            ),
        )
        review = AgentStep(
            agent_name="Reviewer",
            role="Evalua soporte, riesgos y limitaciones.",
            content=review_content,
        )

        final_content = self.llm.chat(
            system_prompt=FINAL_WRITER_SYSTEM_PROMPT,
            user_prompt=build_final_writer_prompt(
                question=question,
                evidence_context=evidence_context,
                research=research.content,
                review=review.content,
            ),
        )
        final_answer = AgentStep(
            agent_name="Final Writer",
            role="Entrega la respuesta final ajustada.",
            content=final_content,
        )

        return MultiAgentResult(
            question=question,
            model=self.model_name,
            retrieved_evidence=evidence,
            plan=plan,
            research=research,
            draft=draft,
            review=review,
            final_answer=final_answer,
        )

    def retrieve_evidence(self, question: str) -> list[RetrievedEvidence]:
        """Retrieve relevant chunks with a transparent keyword baseline."""

        scored_chunks = [
            (
                score_chunk(question, chunk),
                chunk,
            )
            for chunk in self._load_chunks()
        ]
        ranked_chunks = sorted(
            scored_chunks,
            key=lambda item: (item[0], item[1].chunk_id),
            reverse=True,
        )

        return [
            RetrievedEvidence(
                chunk_id=chunk.chunk_id,
                source=chunk.source,
                section=chunk.section,
                text=chunk.text,
                score=score,
            )
            for score, chunk in ranked_chunks[: self.top_k]
        ]

    def _load_chunks(self) -> list[DocumentChunk]:
        """Load and chunk the business case documents once."""

        if self._chunks is not None:
            return self._chunks

        chunks: list[DocumentChunk] = []
        for source_name, content in load_business_case_documents(
            self.documents_dir
        ).items():
            chunks.extend(
                chunk_markdown_by_sections(
                    content=content,
                    source=source_name,
                    max_chars=1100,
                )
            )

        self._chunks = renumber_chunks(chunks)
        return self._chunks


def score_chunk(question: str, chunk: DocumentChunk) -> int:
    """Score chunks with simple lexical overlap for classroom transparency."""

    query_terms = normalize_terms(question)
    chunk_terms = normalize_terms(f"{chunk.section} {chunk.text}")
    return len(query_terms.intersection(chunk_terms))


def load_business_case_documents(directory: Path) -> dict[str, str]:
    """Load markdown business documents, with a built-in fallback for main."""

    if directory.exists():
        documents = sorted(directory.glob("*.md"))
        if documents:
            return {
                str(document_path): normalize_markdown(
                    document_path.read_text(encoding="utf-8")
                )
                for document_path in documents
            }

    return FALLBACK_BUSINESS_CASE


def chunk_markdown_by_sections(
    content: str,
    source: str,
    max_chars: int = 1100,
) -> list[DocumentChunk]:
    """Split a markdown document into simple heading-based chunks."""

    sections: list[tuple[str, list[str]]] = []
    current_title = Path(source).stem
    current_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = stripped.lstrip("#").strip() or current_title
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    chunks: list[DocumentChunk] = []
    for section_title, section_lines in sections:
        section_text = normalize_markdown("\n".join(section_lines))
        for part in split_text(section_text, max_chars=max_chars):
            chunks.append(
                DocumentChunk(
                    chunk_id=f"chunk_{len(chunks) + 1:03d}",
                    text=part,
                    source=source,
                    section=section_title,
                    position=len(chunks) + 1,
                )
            )

    return chunks


def split_text(text: str, max_chars: int) -> list[str]:
    """Split text into readable chunks without external dependencies."""

    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n")]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if not paragraph:
            continue
        candidate = f"{current}\n\n{paragraph}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = paragraph

    if current:
        chunks.append(current)

    return chunks


def normalize_markdown(content: str) -> str:
    """Normalize markdown separators while preserving headings."""

    normalized_lines = [
        line.rstrip()
        for line in content.splitlines()
        if line.strip() != "---"
    ]
    return "\n".join(normalized_lines).strip()


def normalize_terms(text: str) -> set[str]:
    """Normalize text into rough Spanish-friendly keyword terms."""

    stopwords = {
        "a",
        "al",
        "con",
        "de",
        "del",
        "debe",
        "el",
        "en",
        "la",
        "las",
        "los",
        "para",
        "por",
        "que",
        "si",
        "un",
        "una",
        "y",
    }
    cleaned = "".join(
        character.lower() if character.isalnum() else " " for character in text
    )
    return {
        term
        for term in cleaned.split()
        if len(term) > 2 and term not in stopwords
    }


def renumber_chunks(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    """Ensure chunk ids remain unique after combining documents."""

    return [
        DocumentChunk(
            chunk_id=f"chunk_{index:03d}",
            text=chunk.text,
            source=chunk.source,
            section=chunk.section,
            position=index,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]
