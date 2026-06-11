"""RAG assistant for the course session on Retrieval-Augmented Generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ollama

from .chunker import DocumentChunk, chunk_markdown_by_sections
from .document_loader import (
    DEFAULT_BUSINESS_CASE_DIR,
    DEFAULT_SESSION_PATH,
    list_markdown_documents,
    load_markdown_document,
)
from .pdf_loader import chunk_pdf_pages, load_pdf_document
from .prompts import BASELINE_SYSTEM_PROMPT, SYSTEM_PROMPT, build_rag_prompt
from .vector_store import (
    ChromaCourseVectorStore,
    OllamaEmbeddingFunction,
    RetrievedChunk,
)


@dataclass(frozen=True)
class RAGAgentResponse:
    """Final response returned by the RAG assistant."""

    content: str
    model: str
    retrieved_chunks: list[RetrievedChunk]


class RAGCourseAssistant:
    """Course assistant that answers questions using retrieved documents."""

    def __init__(
        self,
        model_name: str = "qwen2.5:3b",
        embedding_model_name: str = "nomic-embed-text",
        document_path: str | Path | None = DEFAULT_SESSION_PATH,
        document_paths: list[str | Path] | None = None,
        vector_store: ChromaCourseVectorStore | None = None,
    ) -> None:
        self.model_name = model_name
        self.embedding_model_name = embedding_model_name
        if document_paths is not None:
            self.document_paths = [Path(path) for path in document_paths]
        elif document_path is not None:
            self.document_paths = [Path(document_path)]
        else:
            self.document_paths = list_markdown_documents(DEFAULT_BUSINESS_CASE_DIR)
        self.vector_store = vector_store or ChromaCourseVectorStore(
            embedding_function=OllamaEmbeddingFunction(embedding_model_name)
        )

    def build_chunks(self, max_chars: int = 1400) -> list[DocumentChunk]:
        """Load documents and split them into retrieval chunks."""

        chunks: list[DocumentChunk] = []

        for document_path in self.document_paths:
            if document_path.suffix.lower() == ".pdf":
                pages = load_pdf_document(document_path)
                document_chunks = chunk_pdf_pages(
                    pages=pages,
                    max_chars=max_chars,
                )
            else:
                content = load_markdown_document(document_path)
                document_chunks = chunk_markdown_by_sections(
                    content=content,
                    source=str(document_path),
                    max_chars=max_chars,
                )
            chunks.extend(document_chunks)

        return renumber_chunks(chunks)

    def index_course_content(self, reset: bool = True) -> int:
        """Index the configured documents in the vector store."""

        chunks = self.build_chunks()
        return self.vector_store.index_chunks(chunks, reset=reset)

    def answer(self, question: str, top_k: int = 4) -> RAGAgentResponse:
        """Answer a question using retrieved context from indexed documents."""

        retrieved_chunks = self.vector_store.query(question=question, top_k=top_k)
        context = "\n\n---\n\n".join(
            chunk.to_context_block() for chunk in retrieved_chunks
        )
        prompt = build_rag_prompt(question=question, retrieved_context=context)

        response: dict[str, Any] = ollama.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        return RAGAgentResponse(
            content=response["message"]["content"],
            model=self.model_name,
            retrieved_chunks=retrieved_chunks,
        )

    def answer_without_rag(self, question: str) -> str:
        """Generate a baseline answer without retrieval for classroom comparison."""

        response: dict[str, Any] = ollama.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
        )

        return response["message"]["content"]


def renumber_chunks(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    """Ensure chunk ids are unique after combining multiple documents."""

    renumbered: list[DocumentChunk] = []

    for index, chunk in enumerate(chunks, start=1):
        renumbered.append(
            DocumentChunk(
                chunk_id=f"chunk_{index:03d}",
                text=chunk.text,
                source=chunk.source,
                section=chunk.section,
                position=index,
                page=chunk.page,
            )
        )

    return renumbered
