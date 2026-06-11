"""RAG course assistant package.

The main agent depends on Ollama at runtime. Import it from
``agents.rag_course_assistant.agent`` when the environment is installed.
"""

__all__ = ["RAGAgentResponse", "RAGCourseAssistant"]


def __getattr__(name: str):
    """Load agent classes lazily to keep utility imports lightweight."""

    if name in __all__:
        from .agent import RAGAgentResponse, RAGCourseAssistant

        return {
            "RAGAgentResponse": RAGAgentResponse,
            "RAGCourseAssistant": RAGCourseAssistant,
        }[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
