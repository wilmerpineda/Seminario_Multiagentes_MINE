"""CLI shared by students, automation scripts and the Codex plugin."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.intelligent_workflow import IntelligentWorkflow, RandomForestConfig, WorkflowRequest, WorkflowResult


DEFAULT_QUESTION = "Que descuento debe probar NovaRetail en clientes de alto valor de Pereira?"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "session7"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Session 7 supervised multi-agent workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run and persist a workflow")
    run_parser.add_argument("--question", default=DEFAULT_QUESTION)
    run_parser.add_argument("--city", default="Pereira")
    run_parser.add_argument("--segment", default="Alto valor")
    run_parser.add_argument("--model", default="qwen2.5:3b")
    run_parser.add_argument("--discounts", default="0,5,10,15,20")
    run_parser.add_argument("--n-estimators", type=int, default=200)
    run_parser.add_argument("--max-depth", type=int, default=10)
    run_parser.add_argument("--output", type=Path)

    ask_parser = subparsers.add_parser("ask", help="Ask about a persisted workflow")
    ask_parser.add_argument("--run", type=Path, required=True)
    ask_parser.add_argument("--question", required=True)
    return parser


def run_workflow(args: argparse.Namespace) -> int:
    request = WorkflowRequest(
        question=args.question,
        city=args.city,
        segment=args.segment,
        discount_options=[int(value.strip()) for value in args.discounts.split(",")],
        model_name=args.model,
        forest=RandomForestConfig(n_estimators=args.n_estimators, max_depth=args.max_depth),
    )
    result = IntelligentWorkflow(model_name=args.model).run(request)
    output = args.output or DEFAULT_OUTPUT_DIR / f"{result.run_id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(result.report_markdown)
    print(f"\nRUN_FILE={output.resolve()}")
    return 0


def ask_workflow(args: argparse.Namespace) -> int:
    result = WorkflowResult.model_validate_json(args.run.read_text(encoding="utf-8"))
    answer = IntelligentWorkflow(model_name=result.request.model_name).answer_follow_up(result, args.question)
    print(json.dumps(answer.model_dump(), ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "run":
        return run_workflow(args)
    return ask_workflow(args)


if __name__ == "__main__":
    raise SystemExit(main())
