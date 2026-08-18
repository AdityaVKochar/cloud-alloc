from __future__ import annotations

import json

import pandas as pd

from cloudalloc.baseline import forecast_metrics, persistence_predictions, run_persistence_baseline
from cloudalloc.constants import INTERVAL_MICROSECONDS
from cloudalloc.ingestion import ingest_frame
from cloudalloc.models import EvaluationMetric, Experiment, Prediction
from cloudalloc.sample_data import synthetic_frame


def test_persistence_does_not_cross_gap():
    frame = pd.DataFrame(
        {
            "task_id": [1, 1, 1],
            "start_time": [0, INTERVAL_MICROSECONDS, 3 * INTERVAL_MICROSECONDS],
            "split": ["train", "train", "validation"],
            "average_cpu": [0.1, 0.2, 0.4],
            "maximum_cpu": [0.2, 0.3, 0.5],
            "average_memory": [0.2, 0.3, 0.5],
            "maximum_memory": [0.3, 0.4, 0.6],
            "request_cpu": [0.6] * 3,
            "request_memory": [0.7] * 3,
        }
    )
    predictions = persistence_predictions(frame)
    assert len(predictions) == 1
    assert predictions.iloc[0]["target_time"] == INTERVAL_MICROSECONDS


def test_forecast_metrics_are_zero_for_perfect_prediction():
    result = forecast_metrics([0.0, 1.0, 2.0], [0.0, 1.0, 2.0])
    assert result["mae"] == 0
    assert result["rmse"] == 0
    assert result["smape"] == 0
    assert result["r2"] == 1


def test_baseline_is_persisted(app, tmp_path):
    with app.app_context():
        ingest_frame(synthetic_frame(task_count=3, intervals=36))
        output = tmp_path / "baseline.json"
        experiment, report = run_persistence_baseline("fixture-v1", output)
        assert experiment.status == "completed"
        assert report["splits"]["validation"]["cpu"]["mae"] >= 0
        assert output.exists()
        assert json.loads(output.read_text())["experiment_id"] == experiment.id
        assert Experiment.query.count() == 1
        assert Prediction.query.count() > 0
        assert EvaluationMetric.query.count() == 8
        assert set(report["splits"]) == {"validation"}
