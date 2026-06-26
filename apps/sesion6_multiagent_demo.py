"""CLI demo for session 6 multi-agent collaboration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.multiagent_collaboration import ClassroomMultiAgentSystem


DEFAULT_QUESTION = (
    "Debe NovaRetail lanzar descuentos agresivos en ciudades intermedias "
    "durante Q4 para recuperar ventas?"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the session 6 multi-agent workflow with Ollama."
    )
    parser.add_argument(
        "--question",
        default=DEFAULT_QUESTION,
        help="Business question to answer.",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5:3b",
        help="Local Ollama model name.",
    )
    args = parser.parse_args()

    system = ClassroomMultiAgentSystem(model_name=args.model)
    result = system.answer(args.question)

    print(f"\nPregunta: {result.question}")
    print(f"Modelo: {result.model}")
    print("\nEvidencia recuperada:")
    for item in result.retrieved_evidence:
        print(f"- {item.chunk_id} | {item.score} | {item.section} | {item.source}")

    for step in result.steps:
        print("\n" + "=" * 80)
        print(f"{step.agent_name} - {step.role}")
        print("=" * 80)
        print(step.content)


if __name__ == "__main__":
    main()
