"""Document loading utilities for the RAG course assistant."""

from __future__ import annotations

from pathlib import Path


DEFAULT_SESSION_PATH = (
    Path(__file__).resolve().parents[2] / "book" / "sesion4_rag.md"
)

DEFAULT_BUSINESS_CASE_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "rag_business_case"
)


def load_markdown_document(path: str | Path = DEFAULT_SESSION_PATH) -> str:
    """Load a markdown document as plain text."""

    document_path = Path(path)
    if not document_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    content = document_path.read_text(encoding="utf-8")
    return normalize_markdown(content)


def load_markdown_documents(paths: list[str | Path]) -> dict[Path, str]:
    """Load multiple markdown documents keyed by path."""

    return {Path(path): load_markdown_document(path) for path in paths}


def list_markdown_documents(directory: str | Path) -> list[Path]:
    """List markdown documents from a directory in stable order."""

    document_dir = Path(directory)
    if not document_dir.exists():
        raise FileNotFoundError(f"Document directory not found: {document_dir}")

    documents = sorted(document_dir.glob("*.md"))
    if not documents:
        raise ValueError(f"No markdown documents found in: {document_dir}")

    return documents


def normalize_markdown(content: str) -> str:
    """Normalize simple markdown separators while preserving headings."""

    normalized_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "---":
            continue
        normalized_lines.append(line.rstrip())

    return "\n".join(normalized_lines).strip()
