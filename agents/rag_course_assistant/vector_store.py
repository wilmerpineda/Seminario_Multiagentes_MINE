"""Vector store utilities backed by ChromaDB and Ollama embeddings."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any

from .chunker import DocumentChunk


DEFAULT_CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned by semantic retrieval."""

    chunk_id: str
    text: str
    source: str
    section: str
    distance: float | None
    page: int | None = None

    def to_context_block(self) -> str:
        """Format this chunk for inclusion in the RAG prompt."""

        page_line = f"Pagina: {self.page}\n" if self.page is not None else ""
        return (
            f"[{self.chunk_id}]\n"
            f"Fuente: {self.source}\n"
            f"{page_line}"
            f"Seccion: {self.section}\n"
            f"Texto:\n{self.text}"
        )


class OllamaEmbeddingFunction:
    """Small embedding adapter that keeps provider details out of Chroma calls."""

    def __init__(self, model_name: str = "nomic-embed-text") -> None:
        self.model_name = model_name

    def embed(self, text: str) -> list[float]:
        """Create one embedding with Ollama."""

        try:
            import ollama
        except ImportError as exc:
            raise ImportError(
                "ollama is required to create embeddings. "
                "Install dependencies with poetry install."
            ) from exc

        try:
            response: dict[str, Any] = ollama.embeddings(
                model=self.model_name,
                prompt=text,
            )
            return list(response["embedding"])
        except AttributeError:
            response = ollama.embed(model=self.model_name, input=text)
            return list(response["embeddings"][0])

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for multiple texts."""

        return [self.embed(text) for text in texts]


class LocalHashEmbeddingFunction:
    """Offline embedding fallback based on hashed word counts.

    This is useful for classroom execution when the Ollama embedding model has
    not been downloaded yet. It is less semantic than a real embedding model,
    but it keeps the vector-store workflow executable.
    """

    def __init__(self, dimensions: int = 384) -> None:
        if dimensions < 32:
            raise ValueError("dimensions must be at least 32.")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        """Create a deterministic sparse vector from normalized tokens."""

        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-záéíóúñü0-9]+", text.lower())

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0

        norm = sum(value * value for value in vector) ** 0.5
        if norm == 0:
            return vector

        return [value / norm for value in vector]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for multiple texts."""

        return [self.embed(text) for text in texts]


class ChromaCourseVectorStore:
    """Persistent ChromaDB vector store for course chunks."""

    def __init__(
        self,
        persist_directory: str | Path = DEFAULT_CHROMA_DIR,
        collection_name: str = "sesion4_rag",
        embedding_function: Any | None = None,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.embedding_function = embedding_function or OllamaEmbeddingFunction()
        self._client = None
        self._collection = None

    @property
    def client(self) -> Any:
        """Return the persistent Chroma client, creating it lazily."""

        if self._client is None:
            try:
                import chromadb
            except ImportError as exc:
                raise ImportError(
                    "chromadb is required for semantic retrieval. "
                    "Install dependencies with poetry install."
                ) from exc

            self._client = chromadb.PersistentClient(path=str(self.persist_directory))

        return self._client

    @property
    def collection(self) -> Any:
        """Return the Chroma collection, creating it lazily."""

        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Chunks from session 4 RAG course content"},
            )

        return self._collection

    def reset_collection(self) -> None:
        """Delete and recreate the collection.

        Chroma collections keep the first embedding dimension they receive.
        Deleting only records is not enough when switching from the local hash
        fallback to a real embedding model.
        """

        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass

        self._collection = None

    def index_chunks(self, chunks: list[DocumentChunk], reset: bool = False) -> int:
        """Index chunks in ChromaDB and return the number of indexed chunks."""

        if not chunks:
            raise ValueError("Cannot index an empty chunk list.")

        if reset:
            self.reset_collection()

        collection = self.collection

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        embeddings = self.embedding_function.embed_many(documents)

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        return len(chunks)

    def query(self, question: str, top_k: int = 4) -> list[RetrievedChunk]:
        """Retrieve the most relevant chunks for a question."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        query_embedding = self.embedding_function.embed(question)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(metadata.get("chunk_id", "")),
                    text=document,
                    source=str(metadata.get("source", "")),
                    section=str(metadata.get("section", "")),
                    distance=float(distance) if distance is not None else None,
                    page=_coerce_page(metadata.get("page")),
                )
            )

        return retrieved


def _coerce_page(value: Any) -> int | None:
    """Convert optional Chroma metadata page values to integers."""

    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
