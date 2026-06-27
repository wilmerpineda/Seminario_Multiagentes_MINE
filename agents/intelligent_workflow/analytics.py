"""Synthetic campaign data, model training and discount simulation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .contracts import ModelMetrics, RandomForestConfig, ScenarioPrediction


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CAMPAIGN_DATA = PROJECT_ROOT / "data" / "session7_discount_campaigns.csv"

CATEGORICAL_FEATURES = ["city", "segment", "channel", "category"]
NUMERIC_FEATURES = [
    "discount_pct",
    "baseline_orders",
    "avg_ticket",
    "unit_cost",
    "logistics_capacity",
    "seasonality_index",
    "baseline_return_rate",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "incremental_orders_pct"


@dataclass
class ModelBundle:
    """Fitted pipeline plus the metrics needed by the workflow."""

    pipeline: Pipeline
    metrics: ModelMetrics
    config: RandomForestConfig


def generate_campaign_data(
    output_path: str | Path = DEFAULT_CAMPAIGN_DATA,
    rows: int = 1200,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a reproducible, explicitly synthetic campaign dataset."""

    rng = np.random.default_rng(seed)
    cities = np.array(["Pereira", "Bucaramanga", "Manizales", "Bogota", "Medellin"])
    segments = np.array(["Alto valor", "Frecuente", "Ocasional", "En riesgo"])
    channels = np.array(["Digital", "Tienda", "B2B"])
    categories = np.array(["Tecnologia", "Hogar", "Bienestar", "Educacion"])

    city = rng.choice(cities, rows)
    segment = rng.choice(segments, rows, p=[0.2, 0.35, 0.3, 0.15])
    channel = rng.choice(channels, rows, p=[0.5, 0.35, 0.15])
    category = rng.choice(categories, rows)
    discount = rng.choice([0, 5, 10, 15, 20, 25], rows, p=[0.08, 0.15, 0.25, 0.25, 0.2, 0.07])
    baseline_orders = rng.integers(80, 700, rows)
    avg_ticket = rng.normal(260_000, 75_000, rows).clip(80_000, 600_000)
    cost_ratio = rng.uniform(0.52, 0.76, rows)
    unit_cost = avg_ticket * cost_ratio
    logistics_capacity = rng.uniform(0.55, 1.0, rows)
    seasonality = rng.uniform(0.8, 1.25, rows)
    return_rate = rng.uniform(0.015, 0.12, rows)

    segment_effect = pd.Series(segment).map(
        {"Alto valor": 4.0, "Frecuente": 2.5, "Ocasional": 1.0, "En riesgo": 5.0}
    ).to_numpy()
    channel_effect = pd.Series(channel).map({"Digital": 3.0, "Tienda": 0.5, "B2B": -1.0}).to_numpy()
    saturation = -0.035 * np.square(discount)
    uplift = (
        0.95 * discount
        + saturation
        + segment_effect
        + channel_effect
        + 12 * (seasonality - 1)
        + 9 * (logistics_capacity - 0.75)
        + rng.normal(0, 2.8, rows)
    ).clip(-6, 32)

    frame = pd.DataFrame(
        {
            "campaign_id": [f"CMP-{index + 1:04d}" for index in range(rows)],
            "city": city,
            "segment": segment,
            "channel": channel,
            "category": category,
            "discount_pct": discount,
            "baseline_orders": baseline_orders,
            "avg_ticket": avg_ticket.round(0),
            "unit_cost": unit_cost.round(0),
            "logistics_capacity": logistics_capacity.round(3),
            "seasonality_index": seasonality.round(3),
            "baseline_return_rate": return_rate.round(3),
            TARGET: uplift.round(3),
        }
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    return frame


def load_campaign_data(path: str | Path = DEFAULT_CAMPAIGN_DATA) -> pd.DataFrame:
    """Load the classroom dataset, generating it when absent."""

    data_path = Path(path)
    if not data_path.exists():
        return generate_campaign_data(data_path)
    return pd.read_csv(data_path)


def train_discount_model(
    data: pd.DataFrame,
    config: RandomForestConfig,
) -> ModelBundle:
    """Fit a transparent sklearn pipeline and calculate train/test metrics."""

    missing = sorted(set(FEATURES + [TARGET]).difference(data.columns))
    if missing:
        raise ValueError(f"Missing campaign columns: {', '.join(missing)}")

    train_x, test_x, train_y, test_y = train_test_split(
        data[FEATURES],
        data[TARGET],
        test_size=config.test_size,
        random_state=config.random_state,
    )
    preprocessor = ColumnTransformer(
        [
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )
    model = RandomForestRegressor(
        n_estimators=config.n_estimators,
        max_depth=config.max_depth,
        min_samples_leaf=config.min_samples_leaf,
        min_samples_split=config.min_samples_split,
        max_features=config.max_features,
        bootstrap=config.bootstrap,
        random_state=config.random_state,
        n_jobs=-1,
    )
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", model)])

    started = perf_counter()
    pipeline.fit(train_x, train_y)
    elapsed = perf_counter() - started
    train_prediction = pipeline.predict(train_x)
    test_prediction = pipeline.predict(test_x)

    feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
    importances = pipeline.named_steps["model"].feature_importances_
    ranked = sorted(zip(feature_names, importances), key=lambda item: item[1], reverse=True)
    top_features = {name.replace("categorical__", "").replace("numeric__", ""): round(float(value), 4) for name, value in ranked[:10]}

    train_r2 = float(r2_score(train_y, train_prediction))
    test_r2 = float(r2_score(test_y, test_prediction))
    metrics = ModelMetrics(
        train_mae=round(float(mean_absolute_error(train_y, train_prediction)), 3),
        test_mae=round(float(mean_absolute_error(test_y, test_prediction)), 3),
        train_r2=round(train_r2, 3),
        test_r2=round(test_r2, 3),
        training_seconds=round(elapsed, 3),
        overfit_gap=round(train_r2 - test_r2, 3),
        feature_importance=top_features,
    )
    return ModelBundle(pipeline=pipeline, metrics=metrics, config=config)


def simulate_discount_scenarios(
    data: pd.DataFrame,
    bundle: ModelBundle,
    city: str,
    segment: str,
    discounts: list[int],
) -> list[ScenarioPrediction]:
    """Predict demand and apply deterministic business formulas."""

    cohort = data[(data["city"] == city) & (data["segment"] == segment)]
    if cohort.empty:
        cohort = data[data["city"] == city]
    if cohort.empty:
        cohort = data

    representative = {
        "city": city,
        "segment": segment,
        "channel": cohort["channel"].mode().iloc[0],
        "category": cohort["category"].mode().iloc[0],
        "baseline_orders": float(cohort["baseline_orders"].median()),
        "avg_ticket": float(cohort["avg_ticket"].median()),
        "unit_cost": float(cohort["unit_cost"].median()),
        "logistics_capacity": float(cohort["logistics_capacity"].median()),
        "seasonality_index": float(cohort["seasonality_index"].median()),
        "baseline_return_rate": float(cohort["baseline_return_rate"].median()),
    }
    rows = [{**representative, "discount_pct": discount} for discount in discounts]
    scenario_frame = pd.DataFrame(rows)[FEATURES]
    predicted_uplift = bundle.pipeline.predict(scenario_frame)

    scenarios: list[ScenarioPrediction] = []
    for discount, uplift in zip(discounts, predicted_uplift):
        orders = representative["baseline_orders"] * (1 + float(uplift) / 100)
        net_ticket = representative["avg_ticket"] * (1 - discount / 100)
        revenue = orders * net_ticket
        product_cost = orders * representative["unit_cost"]
        return_cost = revenue * representative["baseline_return_rate"]
        logistics_cost = orders * 7_000 * (1.25 - representative["logistics_capacity"])
        margin = revenue - product_cost - return_cost - logistics_cost
        scenarios.append(
            ScenarioPrediction(
                discount_pct=discount,
                predicted_uplift_pct=round(float(uplift), 2),
                expected_orders=round(orders, 1),
                expected_revenue=round(revenue, 0),
                expected_margin=round(margin, 0),
                margin_pct=round(100 * margin / revenue, 2) if revenue else 0,
            )
        )
    return scenarios
