from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .adapters import SystemUnderTest
from .contracts import CostEstimate, EvaluationCase, EvaluationRun
from .metrics import evaluate_response


def load_cases(path: str | Path) -> list[EvaluationCase]:
    source = Path(path)
    return [
        EvaluationCase.model_validate_json(line)
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class EvaluationSuite:
    def __init__(
        self,
        adapter: SystemUnderTest,
        *,
        input_cost_per_million: float = 0.0,
        output_cost_per_million: float = 0.0,
        budget: float = 0.10,
    ):
        self.adapter = adapter
        self.input_cost_per_million = input_cost_per_million
        self.output_cost_per_million = output_cost_per_million
        self.budget = budget

    def run(self, cases: list[EvaluationCase]) -> EvaluationRun:
        results = []
        metric_scores: dict[str, list[float]] = defaultdict(list)
        cohort_passes: dict[str, list[float]] = defaultdict(list)
        input_tokens = 0
        output_tokens = 0
        model_calls = 0

        for case in cases:
            response = self.adapter.execute(case)
            metrics = evaluate_response(case, response)
            from .contracts import CaseResult

            case_result = CaseResult(case=case, response=response, metrics=metrics)
            results.append(case_result)
            for metric in metrics:
                metric_scores[metric.metric].append(metric.score)
            if case.cohort:
                cohort_passes[case.cohort.name].append(1.0 if case_result.passed else 0.0)

            input_tokens += max(1, len(case.question.split()) * 2)
            output_tokens += max(1, len(response.summary.split()) * 2)
            model_calls += sum(
                1
                for trace in response.traces
                if trace.get("agent") in {"executive_writer", "insight_agent"}
            )

        aggregate_scores = {
            metric: round(sum(values) / len(values), 4)
            for metric, values in metric_scores.items()
        }
        cohort_scores = {
            cohort: round(sum(values) / len(values), 4)
            for cohort, values in cohort_passes.items()
        }
        worst_cohort = min(cohort_scores, key=cohort_scores.get) if cohort_scores else None
        disparity_gap = (
            round(max(cohort_scores.values()) - min(cohort_scores.values()), 4)
            if len(cohort_scores) > 1
            else 0.0
        )
        estimated_cost = (
            input_tokens * self.input_cost_per_million
            + output_tokens * self.output_cost_per_million
        ) / 1_000_000
        cost = CostEstimate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_calls=model_calls,
            estimated_cost=round(estimated_cost, 6),
            budget=self.budget,
            budget_exceeded=estimated_cost > self.budget,
        )
        return EvaluationRun(
            system_name=self.adapter.name,
            results=results,
            aggregate_scores=aggregate_scores,
            cohort_scores=cohort_scores,
            worst_cohort=worst_cohort,
            disparity_gap=disparity_gap,
            cost=cost,
        )

