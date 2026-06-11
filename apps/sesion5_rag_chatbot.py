"""Streamlit chatbot for session 5: RAG over public BI documents."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.rag_course_assistant.agent import RAGCourseAssistant
from agents.rag_course_assistant.evaluation import evaluate_answer
from agents.rag_course_assistant.vector_store import (
    ChromaCourseVectorStore,
    OllamaEmbeddingFunction,
)


PERSIST_DIR = PROJECT_ROOT / "agents" / "rag_course_assistant" / "chroma_db"
COLLECTION_NAME = "sesion5_rag_pdf_chatbot"
UPLOAD_DIR = PROJECT_ROOT / "data" / "sesion5_uploaded_docs"


def main() -> None:
    st.set_page_config(page_title="Sesion 5 - Chatbot RAG", layout="wide")
    st.title("Sesion 5 - Chatbot RAG Empresarial")

    with st.sidebar:
        st.header("Base documental")
        uploaded_files = st.file_uploader(
            "Cargar PDFs o Markdown",
            type=["pdf", "md"],
            accept_multiple_files=True,
        )
        model_name = st.text_input("Modelo Ollama", value="qwen2.5:3b")
        embedding_model = st.text_input("Modelo de embeddings", value="nomic-embed-text")
        top_k = st.slider("Chunks recuperados", min_value=2, max_value=8, value=5)

        if st.button("Indexar documentos", type="primary", use_container_width=True):
            if not uploaded_files:
                st.warning("Carga al menos un PDF o Markdown antes de indexar.")
            else:
                index_uploaded_documents(uploaded_files, model_name, embedding_model)

        st.divider()
        st.caption("Fuentes sugeridas: Banco Mundial OKR, OCDE o Stanford AI Index.")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "assistant" not in st.session_state:
        st.session_state.assistant = build_assistant(model_name, embedding_model)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Pregunta sobre la base documental indexada")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Recuperando evidencia y generando respuesta..."):
                response = st.session_state.assistant.answer(question, top_k=top_k)
                evaluation = evaluate_answer(
                    question=question,
                    answer=response.content,
                    retrieved_chunks=response.retrieved_chunks,
                )
            st.markdown(response.content)
            st.session_state.messages.append(
                {"role": "assistant", "content": response.content}
            )

            with st.expander("Evidencia recuperada", expanded=True):
                for chunk in response.retrieved_chunks:
                    page = f" pagina {chunk.page}" if chunk.page else ""
                    st.markdown(
                        f"**{chunk.chunk_id}** - `{Path(chunk.source).name}`{page} "
                        f"- distancia `{chunk.distance:.4f}`"
                        if chunk.distance is not None
                        else f"**{chunk.chunk_id}** - `{Path(chunk.source).name}`{page}"
                    )
                    st.write(chunk.text[:1200])

            with st.expander("Evaluacion de grounding"):
                st.write(
                    {
                        "relevance": evaluation.relevance,
                        "grounding": evaluation.grounding,
                        "source_use": evaluation.source_use,
                        "passed": evaluation.passed,
                        "risk_notes": evaluation.risk_notes,
                    }
                )


def index_uploaded_documents(uploaded_files, model_name: str, embedding_model: str) -> None:
    """Persist uploaded files for traceable source metadata and index them."""

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    document_paths: list[Path] = []
    for uploaded_file in uploaded_files:
        path = UPLOAD_DIR / safe_filename(uploaded_file.name)
        path.write_bytes(uploaded_file.getbuffer())
        document_paths.append(path)

    assistant = build_assistant(
        model_name=model_name,
        embedding_model=embedding_model,
        document_paths=document_paths,
    )
    indexed = assistant.index_course_content(reset=True)
    st.session_state.assistant = build_assistant(model_name, embedding_model)
    st.success(f"Documentos indexados: {len(document_paths)}. Chunks creados: {indexed}.")


def safe_filename(filename: str) -> str:
    """Return a conservative filename for uploaded course documents."""

    return Path(filename).name.replace(" ", "_")


def build_assistant(
    model_name: str,
    embedding_model: str,
    document_paths: list[Path] | None = None,
) -> RAGCourseAssistant:
    """Create the session 5 assistant using a dedicated Chroma collection."""

    store = ChromaCourseVectorStore(
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=OllamaEmbeddingFunction(embedding_model),
    )
    return RAGCourseAssistant(
        model_name=model_name,
        embedding_model_name=embedding_model,
        document_path=None,
        document_paths=document_paths,
        vector_store=store,
    )


if __name__ == "__main__":
    main()
