"""Reusable classifier supplied to both session 7 teams."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


@dataclass
class ClassifierBundle:
    pipeline: Pipeline
    precision: float
    recall: float
    f1: float


def train_classifier(
    data: pd.DataFrame,
    target: str,
    categorical: list[str],
    numeric: list[str],
    random_state: int = 42,
) -> ClassifierBundle:
    """Train the supplied baseline so teams can focus on orchestration."""

    train_x, test_x, train_y, test_y = train_test_split(
        data[categorical + numeric],
        data[target],
        test_size=0.25,
        random_state=random_state,
        stratify=data[target],
    )
    pipeline = Pipeline(
        [
            (
                "preprocessor",
                ColumnTransformer(
                    [
                        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
                        ("numeric", "passthrough", numeric),
                    ]
                ),
            ),
            ("model", RandomForestClassifier(n_estimators=150, max_depth=10, random_state=random_state, class_weight="balanced", n_jobs=-1)),
        ]
    )
    pipeline.fit(train_x, train_y)
    prediction = pipeline.predict(test_x)
    return ClassifierBundle(
        pipeline=pipeline,
        precision=round(float(precision_score(test_y, prediction, zero_division=0)), 3),
        recall=round(float(recall_score(test_y, prediction, zero_division=0)), 3),
        f1=round(float(f1_score(test_y, prediction, zero_division=0)), 3),
    )
