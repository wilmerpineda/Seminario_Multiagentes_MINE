"""PDF loading and chunking utilities for the RAG course assistant."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .chunker import DocumentChunk


@dataclass(frozen=True)
class DocumentPage:
    """Plain text extracted from a single PDF page."""

    text: str
    source: str
    page_number: int


def load_pdf_document(path: str | Path) -> list[DocumentPage]:
    """Load a PDF document as plain text pages."""

    document_path = Path(path)
    if not document_path.exists():
        raise FileNotFoundError(f"PDF document not found: {document_path}")

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError(
            "pypdf is required to load PDF documents. "
            "Install dependencies with poetry install."
        ) from exc

    reader = PdfReader(str(document_path))
    pages: list[DocumentPage] = []

    for index, page in enumerate(reader.pages, start=1):
        text = normalize_pdf_text(page.extract_text() or "")
        if text:
            pages.append(
                DocumentPage(
                    text=text,
                    source=str(document_path),
                    page_number=index,
                )
            )

    if not pages:
        raise ValueError(f"No extractable text found in PDF: {document_path}")

    return pages


def chunk_pdf_pages(
    pages: list[DocumentPage],
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> list[DocumentChunk]:
    """Split PDF pages into chunks while preserving source page metadata."""

    if max_chars < 300:
        raise ValueError("max_chars must be at least 300.")
    if overlap_chars < 0:
        raise ValueError("overlap_chars cannot be negative.")
    if overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be smaller than max_chars.")

    chunks: list[DocumentChunk] = []

    for page in pages:
        pieces = split_text_with_overlap(
            page.text,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
        for piece in pieces:
            position = len(chunks) + 1
            chunks.append(
                DocumentChunk(
                    chunk_id=f"chunk_{position:03d}",
                    text=piece,
                    source=page.source,
                    section=f"Pagina {page.page_number}",
                    position=position,
                    page=page.page_number,
                )
            )

    return chunks


def normalize_pdf_text(text: str) -> str:
    """Normalize whitespace from PDF text extraction."""

    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    paragraphs: list[str] = []
    current: list[str] = []

    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line)

    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(paragraphs).strip()


def split_text_with_overlap(
    text: str,
    max_chars: int,
    overlap_chars: int,
) -> list[str]:
    """Split text into paragraph-aware chunks with a small character overlap."""

    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    pieces: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            paragraph_break = text.rfind("\n\n", start, end)
            sentence_break = text.rfind(". ", start, end)
            split_at = max(paragraph_break, sentence_break)
            if split_at > start + max_chars // 2:
                end = split_at + (2 if split_at == paragraph_break else 1)

        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)

        if end >= len(text):
            break

        start = max(end - overlap_chars, start + 1)

    return pieces
