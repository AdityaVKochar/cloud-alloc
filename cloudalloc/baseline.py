from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sqlalchemy import select

from .constants import INTERVAL_MICROSECONDS
from .extensions import db
from .models import EvaluationMetric, Experiment, Prediction, Task, WorkloadSample


def workload_frame() -> pd.DataFrame:
    statement = (
        select(
            WorkloadSample.task_id,
            WorkloadSample.start_time,
            WorkloadSample.split,
            WorkloadSample.average_cpu,
            WorkloadSample.maximum_cpu,
            WorkloadSample.average_memory,
            WorkloadSample.maximum_memory,
            WorkloadSample.request_cpu,
            WorkloadSample.request_memory,
            Task.cell,
            Task.collection_id,
            Task.instance_index,
        )
        .join(Task, Task.id == WorkloadSample.task_id)
        .order_by(WorkloadSample.task_id, WorkloadSample.start_time)
    )
    return pd.read_sql(statement, db.engine)


def persistence_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    """Predict t+1 from t; the exact-interval check prevents predictions across gaps."""
    result = frame.sort_values(["task_id", "start_time"]).copy()
    grouped = result.groupby("task_id", sort=False)
    result["target_time"] = grouped["start_time"].shift(-1)
    result["target_split"] = grouped["split"].shift(-1)
    for resource in ("cpu", "memory"):
        result[f"predicted_{resource}"] = result[f"maximum_{resource}"]
        result[f"actual_{resource}"] = grouped[f"maximum_{resource}"].shift(-1)
        result[f"target_average_{resource}"] = grouped[f"average_{resource}"].shift(-1)
    contiguous = result["target_time"] - result["start_time"] == INTERVAL_MICROSECONDS
    return result[contiguous].dropna(subset=["actual_cpu", "actual_memory"]).reset_index(drop=True)


def forecast_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    denominator = np.abs(actual) + np.abs(predicted)
    ratios = np.zeros_like(denominator, dtype=float)
    np.divide(2 * np.abs(predicted - actual), denominator, out=ratios, where=denominator != 0)
    smape = np.mean(ratios)
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
        "smape": float(smape),
        "r2": float(r2_score(actual, predicted)) if len(actual) > 1 else 0.0,
    }


def run_persistence_baseline(
    dataset_version: str,
    output_path: str | Path,
    *,
    include_test: bool = False,
) -> tuple[Experiment, dict]:
    frame = workload_frame()
    if frame.empty:
        raise ValueError("No workload samples are loaded")
    predictions = persistence_predictions(frame)
    experiment = Experiment(
        name="Persistence baseline",
        model_type="persistence",
        dataset_version=dataset_version,
        parameters={"horizon_intervals": 1, "interval_seconds": 300},
        status="running",
    )
    db.session.add(experiment)
    db.session.flush()

    report: dict[str, dict] = {"experiment_id": experiment.id, "splits": {}}
    evaluated_splits = ("validation", "test") if include_test else ("validation",)
    for split in evaluated_splits:
        subset = predictions[predictions["target_split"] == split]
        if subset.empty:
            continue
        report["splits"][split] = {}
        for resource in ("cpu", "memory"):
            metrics = forecast_metrics(subset[f"actual_{resource}"], subset[f"predicted_{resource}"])
            report["splits"][split][resource] = metrics
            for name, value in metrics.items():
                db.session.add(
                    EvaluationMetric(
                        experiment_id=experiment.id,
                        policy="forecast",
                        resource=resource,
                        split=split,
                        metric_name=name,
                        metric_value=value,
                    )
                )

    prediction_rows = []
    for row in predictions.itertuples(index=False):
        if row.target_split not in set(evaluated_splits):
            continue
        prediction_rows.append(
            {
                "experiment_id": experiment.id,
                "task_id": int(row.task_id),
                "target_time": int(row.target_time),
                "split": row.target_split,
                "predicted_cpu": float(row.predicted_cpu),
                "predicted_memory": float(row.predicted_memory),
                "actual_cpu": float(row.actual_cpu),
                "actual_memory": float(row.actual_memory),
                "average_cpu": float(row.target_average_cpu),
                "average_memory": float(row.target_average_memory),
            }
        )
    if prediction_rows:
        db.session.execute(Prediction.__table__.insert(), prediction_rows)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    experiment.artifact_path = str(output.resolve())
    experiment.validation_summary = report["splits"].get("validation", {})
    experiment.status = "completed"
    experiment.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return experiment, report
