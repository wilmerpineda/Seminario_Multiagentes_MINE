"""Financial Research Agent.

This module defines an agent that can plan tool usage, execute financial tools,
and generate a final market analysis response using a local Ollama model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import ollama

from .prompts import (
    SYSTEM_PROMPT,
    TOOL_PLANNING_PROMPT,
    build_final_answer_prompt,
    build_tool_planning_prompt,
)
from .tools import ToolRegistry


@dataclass
class AgentResponse:
    """Final response returned by the financial agent."""

    content: str
    model: str
    tool_plan: dict[str, Any]
    tool_results: dict[str, Any]


class FinancialResearchAgent:
    """Financial research agent with basic tool-calling capabilities."""

    def __init__(
        self,
        model_name: str = "qwen2.5:3b",
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.model_name = model_name
        self.tool_registry = tool_registry or ToolRegistry()

    def analyze(self, user_question: str) -> AgentResponse:
        """Analyze a financial question using planned tool execution."""

        tool_plan = self._plan_tools(user_question)
        tool_results = self._execute_tool_plan(tool_plan)

        final_prompt = build_final_answer_prompt(
            user_question=user_question,
            tool_results=json.dumps(
                tool_results,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
        )

        response: dict[str, Any] = ollama.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": final_prompt},
            ],
        )

        return AgentResponse(
            content=response["message"]["content"],
            model=self.model_name,
            tool_plan=tool_plan,
            tool_results=tool_results,
        )

    def _plan_tools(self, user_question: str) -> dict[str, Any]:
        """Ask the model which tools should be executed."""

        response: dict[str, Any] = ollama.chat(
            model=self.model_name,
            format="json",
            messages=[
                {"role": "system", "content": TOOL_PLANNING_PROMPT},
                {
                    "role": "user",
                    "content": build_tool_planning_prompt(
                        user_question=user_question,
                        available_tools=self.tool_registry.describe_tools(),
                    ),
                },
            ],
        )

        raw_content = response["message"]["content"]
        return parse_json_tool_plan(raw_content)

    def _execute_tool_plan(self, tool_plan: dict[str, Any]) -> dict[str, Any]:
        """Execute each tool requested in the tool plan."""

        results: dict[str, Any] = {}

        for step_number, tool_call in enumerate(tool_plan.get("tools", []), start=1):
            tool_name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})

            if not tool_name:
                raise ValueError(f"Missing tool name in step {step_number}.")
            if not isinstance(arguments, dict):
                raise ValueError(f"Arguments must be a dictionary in step {step_number}.")

            result = self.tool_registry.run(
                tool_name=tool_name,
                arguments=arguments,
            )

            results[f"step_{step_number}_{tool_name}"] = result

        if not results:
            raise ValueError("The tool plan did not request any tools.")

        return results


def parse_json_tool_plan(raw_content: str) -> dict[str, Any]:
    """Parse a JSON tool plan, accepting plain JSON or fenced JSON."""

    content = raw_content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1]).strip()

    try:
        tool_plan = json.loads(content)
    except json.JSONDecodeError as exc:
        repaired_content = repair_incomplete_json(content)
        try:
            tool_plan = json.loads(repaired_content)
        except json.JSONDecodeError:
            raise ValueError(
                "The model did not return a valid JSON tool plan. "
                f"Raw response was:\n{raw_content}"
            ) from exc

    if not isinstance(tool_plan, dict):
        raise ValueError("The tool plan must be a JSON object.")
    if "tools" not in tool_plan or not isinstance(tool_plan["tools"], list):
        raise ValueError("The tool plan must contain a 'tools' list.")

    return tool_plan


def repair_incomplete_json(content: str) -> str:
    """Repair simple cases where the model omits trailing JSON closers."""

    repaired = content.strip()
    missing_brackets = repaired.count("[") - repaired.count("]")
    missing_braces = repaired.count("{") - repaired.count("}")

    if missing_brackets > 0:
        repaired += "]" * missing_brackets
    if missing_braces > 0:
        repaired += "}" * missing_braces

    return repaired
