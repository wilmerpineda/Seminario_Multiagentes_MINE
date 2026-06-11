"""Chunking utilities for the RAG course assistant."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    """A document fragment with metadata used for retrieval."""

    chunk_id: str
    text: str
    source: str
    section: str
    position: int
    page: int | None = None

    @property
    def metadata(self) -> dict[str, str | int]:
        """Return Chroma-compatible metadata for this chunk."""

        metadata: dict[str, str | int] = {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "section": self.section,
            "position": self.position,
        }
        if self.page is not None:
            metadata["page"] = self.page
        return metadata


def chunk_markdown_by_sections(
    content: str,
    source: str,
    max_chars: int = 1400,
) -> list[DocumentChunk]:
    """Split markdown into chunks, preserving nearby section headings."""

    if max_chars < 300:
        raise ValueError("max_chars must be at least 300.")

    sections = split_markdown_sections(content)
    chunks: list[DocumentChunk] = []

    for section_title, section_text in sections:
        for piece in split_long_text(section_text, max_chars=max_chars):
            position = len(chunks) + 1
            chunks.append(
                DocumentChunk(
                    chunk_id=f"chunk_{position:03d}",
                    text=piece.strip(),
                    source=source,
                    section=section_title,
                    position=position,
                )
            )

    return chunks


def split_markdown_sections(content: str) -> list[tuple[str, str]]:
    """Group markdown content by headings."""

    sections: list[tuple[str, list[str]]] = []
    current_title = "Inicio"
    current_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = stripped.lstrip("#").strip() or "Sin titulo"
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    return [
        (title, "\n".join(lines).strip())
        for title, lines in sections
        if "\n".join(lines).strip()
    ]


def split_long_text(text: str, max_chars: int) -> list[str]:
    """Split long text on paragraph boundaries when possible."""

    if len(text) <= max_chars:
        return [text]

    pieces: list[str] = []
    current: list[str] = []
    current_size = 0

    for paragraph in text.split("\n\n"):
        paragraph_size = len(paragraph) + 2
        if current and current_size + paragraph_size > max_chars:
            pieces.append("\n\n".join(current))
            current = [paragraph]
            current_size = paragraph_size
        else:
            current.append(paragraph)
            current_size += paragraph_size

    if current:
        pieces.append("\n\n".join(current))

    return pieces
