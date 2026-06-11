from __future__ import annotations

from pathlib import Path

from agents.rag_course_assistant.agent import RAGCourseAssistant
from agents.rag_course_assistant.chunker import chunk_markdown_by_sections
from agents.rag_course_assistant.document_loader import (
    DEFAULT_BUSINESS_CASE_DIR,
    list_markdown_documents,
    load_markdown_document,
)
from agents.rag_course_assistant.vector_store import ChromaCourseVectorStore


class FakeEmbeddingFunction:
    def embed(self, text: str) -> list[float]:
        lower = text.lower()
        return [
            float("rag" in lower),
            float("embedding" in lower or "embeddings" in lower),
            float("politicas" in lower or "politica" in lower),
        ]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def test_load_session_4_document() -> None:
    content = load_markdown_document()

    assert "Introduccion a RAG" in content
    assert "Retrieval-Augmented Generation" in content


def test_chunk_markdown_by_sections_returns_metadata() -> None:
    content = """
# Titulo

Texto sobre RAG.

## Embeddings

Texto sobre embeddings.
""".strip()

    chunks = chunk_markdown_by_sections(content, source="demo.md", max_chars=400)

    assert chunks
    assert chunks[0].chunk_id == "chunk_001"
    assert chunks[0].metadata["source"] == "demo.md"
    assert any("Embeddings" in chunk.section for chunk in chunks)


def test_chroma_vector_store_retrieves_relevant_chunks(tmp_path: Path) -> None:
    chunks = chunk_markdown_by_sections(
        """
# RAG

RAG permite recuperar documentos relevantes antes de responder.

# Politicas

Las politicas corporativas pueden consultarse con un asistente documental.
""".strip(),
        source="demo.md",
        max_chars=400,
    )
    store = ChromaCourseVectorStore(
        persist_directory=tmp_path,
        collection_name="test_rag_course",
        embedding_function=FakeEmbeddingFunction(),
    )

    indexed = store.index_chunks(chunks, reset=True)
    results = store.query("Como se consultan politicas corporativas?", top_k=1)

    assert indexed == len(chunks)
    assert results
    assert "politicas" in results[0].text.lower()


def test_business_case_documents_build_unique_chunks() -> None:
    documents = list_markdown_documents(DEFAULT_BUSINESS_CASE_DIR)
    assistant = RAGCourseAssistant(document_paths=documents)

    chunks = assistant.build_chunks(max_chars=900)
    chunk_ids = [chunk.chunk_id for chunk in chunks]

    assert len(documents) == 3
    assert chunks
    assert len(chunk_ids) == len(set(chunk_ids))
    assert any("NovaRetail" in chunk.text for chunk in chunks)
