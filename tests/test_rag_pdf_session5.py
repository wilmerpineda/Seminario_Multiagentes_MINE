from __future__ import annotations

from agents.rag_course_assistant.evaluation import evaluate_answer
from agents.rag_course_assistant.pdf_loader import (
    DocumentPage,
    chunk_pdf_pages,
    normalize_pdf_text,
    split_text_with_overlap,
)
from agents.rag_course_assistant.vector_store import RetrievedChunk


def test_normalize_pdf_text_collapses_spaces_and_keeps_paragraphs() -> None:
    raw_text = "Titulo   del reporte\n\n  Ventas     crecieron  \n margen estable "

    normalized = normalize_pdf_text(raw_text)

    assert normalized == "Titulo del reporte\n\nVentas crecieron margen estable"


def test_chunk_pdf_pages_preserves_page_metadata() -> None:
    pages = [
        DocumentPage(
            text="La adopcion de datos abiertos mejora la toma de decisiones.",
            source="reporte.pdf",
            page_number=3,
        )
    ]

    chunks = chunk_pdf_pages(pages, max_chars=400, overlap_chars=50)

    assert len(chunks) == 1
    assert chunks[0].source == "reporte.pdf"
    assert chunks[0].page == 3
    assert chunks[0].metadata["page"] == 3
    assert chunks[0].section == "Pagina 3"


def test_split_text_with_overlap_creates_multiple_chunks() -> None:
    text = " ".join(f"palabra{i}" for i in range(120))

    pieces = split_text_with_overlap(text, max_chars=320, overlap_chars=40)

    assert len(pieces) > 1
    assert all(len(piece) <= 320 for piece in pieces)


def test_evaluate_answer_passes_when_answer_uses_retrieved_chunk() -> None:
    chunk = RetrievedChunk(
        chunk_id="chunk_001",
        text="Los datos abiertos permiten mejorar decisiones publicas y analitica.",
        source="reporte.pdf",
        section="Pagina 1",
        page=1,
        distance=0.12,
    )

    result = evaluate_answer(
        question="Como ayudan los datos abiertos a la analitica?",
        answer=(
            "Los datos abiertos apoyan la analitica y la toma de decisiones. "
            "Fuentes usadas: chunk_001."
        ),
        retrieved_chunks=[chunk],
    )

    assert result.passed


def test_evaluate_answer_flags_missing_sources() -> None:
    chunk = RetrievedChunk(
        chunk_id="chunk_002",
        text="El reporte menciona calidad documental y trazabilidad.",
        source="reporte.pdf",
        section="Pagina 2",
        page=2,
        distance=0.2,
    )

    result = evaluate_answer(
        question="Que menciona el reporte sobre trazabilidad?",
        answer="El reporte menciona trazabilidad documental.",
        retrieved_chunks=[chunk],
    )

    assert not result.passed
    assert "La respuesta no cita claramente los chunks recuperados." in result.risk_notes
