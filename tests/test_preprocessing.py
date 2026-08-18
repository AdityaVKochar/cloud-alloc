from __future__ import annotations

import json

import pandas as pd
import pytest

from cloudalloc.constants import INTERVAL_MICROSECONDS
from cloudalloc.preprocessing import (
    DataValidationError,
    assign_chronological_splits,
    fill_single_interval_gaps,
    load_manifest,
    prepare_google_trace,
    stable_task_hash,
    validate_frame,
    write_manifest,
)
from cloudalloc.sample_data import synthetic_frame


def test_hash_is_stable_and_key_sensitive():
    assert stable_task_hash(12, 3) == stable_task_hash(12, 3)
    assert stable_task_hash(12, 3) != stable_task_hash(12, 4)


def test_validation_rejects_negative_resources():
    frame = synthetic_frame()
    frame.loc[0, "maximum_cpu"] = -0.1
    with pytest.raises(DataValidationError, match="non-negative"):
        validate_frame(frame)


def test_single_gap_is_filled_from_past_only():
    frame = synthetic_frame(task_count=1, intervals=16)
    assert 8 * INTERVAL_MICROSECONDS not in set(frame["start_time"])
    filled = fill_single_interval_gaps(validate_frame(frame))
    inserted = filled[filled["start_time"] == 8 * INTERVAL_MICROSECONDS].iloc[0]
    previous = filled[filled["start_time"] == 7 * INTERVAL_MICROSECONDS].iloc[0]
    assert inserted["maximum_cpu"] == previous["maximum_cpu"]
    assert inserted["end_time"] == 9 * INTERVAL_MICROSECONDS


def test_splits_are_strictly_chronological():
    split = assign_chronological_splits(validate_frame(synthetic_frame()))
    assert split.loc[split["split"] == "train", "start_time"].max() < split.loc[split["split"] == "validation", "start_time"].min()
    assert split.loc[split["split"] == "validation", "start_time"].max() < split.loc[split["split"] == "test", "start_time"].min()


def test_manifest_detects_tampering(tmp_path):
    data_path = tmp_path / "sample.parquet"
    manifest_path = tmp_path / "manifest.json"
    synthetic_frame().to_parquet(data_path, index=False)
    write_manifest(data_path, manifest_path, source="test", cell="fixture", selection_rule="test")
    metadata, frame = load_manifest(manifest_path)
    assert metadata["row_count"] == len(frame)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(DataValidationError, match="checksum"):
        load_manifest(manifest_path)


def test_google_jsonl_preparation_joins_only_prior_events(tmp_path):
    usage_path = tmp_path / "usage.json"
    event_path = tmp_path / "events.json"
    usage_rows = []
    for interval in range(5):
        usage_rows.append(
            {
                "start_time": str(interval * INTERVAL_MICROSECONDS),
                "end_time": str((interval + 1) * INTERVAL_MICROSECONDS),
                "collection_id": "7",
                "instance_index": "2",
                "average_usage": {"cpus": 0.1 + interval / 100, "memory": 0.2},
                "maximum_usage": {"cpus": 0.2 + interval / 100, "memory": 0.3},
                "assigned_memory": 0.5,
            }
        )
    usage_path.write_text("\n".join(json.dumps(row) for row in usage_rows), encoding="utf-8")
    event_path.write_text(
        "\n".join(
            [
                json.dumps({
                    "time": "0", "collection_id": "7", "instance_index": "2",
                    "scheduling_class": "1", "priority": "100",
                    "resource_request": {"cpus": 0.4, "memory": 0.5},
                }),
                json.dumps({
                    "time": str(10 * INTERVAL_MICROSECONDS), "collection_id": "7", "instance_index": "2",
                    "scheduling_class": "2", "priority": "200",
                    "resource_request": {"cpus": 0.9, "memory": 0.9},
                }),
            ]
        ),
        encoding="utf-8",
    )
    output = prepare_google_trace(
        [usage_path], [event_path], tmp_path / "prepared.parquet",
        days=1, max_tasks=1, minimum_coverage=0.01, candidate_modulus=1,
    )
    prepared = pd.read_parquet(output)
    assert len(prepared) == 5
    assert set(prepared["request_cpu"]) == {0.4}
    assert set(prepared["priority"]) == {100}
