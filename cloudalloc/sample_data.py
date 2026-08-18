from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from .constants import INTERVAL_MICROSECONDS
from .preprocessing import assign_chronological_splits, write_manifest


def synthetic_frame(task_count: int = 4, intervals: int = 36) -> pd.DataFrame:
    """Create a deterministic fixture with trends, periodicity, and one single gap."""
    rows = []
    for task in range(task_count):
        request_cpu = 0.35 + task * 0.08
        request_memory = 0.45 + task * 0.07
        for interval in range(intervals):
            if task == 0 and interval == 8:
                continue
            phase = interval / 5 + task
            avg_cpu = max(0.01, 0.14 + task * 0.035 + 0.07 * math.sin(phase))
            avg_memory = max(0.01, 0.22 + task * 0.04 + 0.05 * math.cos(phase / 2))
            rows.append(
                {
                    "cell": "fixture",
                    "collection_id": 10_000 + task,
                    "instance_index": 0,
                    "start_time": interval * INTERVAL_MICROSECONDS,
                    "end_time": (interval + 1) * INTERVAL_MICROSECONDS,
                    "scheduling_class": task % 4,
                    "priority": 100 + task,
                    "request_cpu": request_cpu,
                    "request_memory": request_memory,
                    "average_cpu": avg_cpu,
                    "maximum_cpu": avg_cpu + 0.035 + (interval % 3) * 0.005,
                    "average_memory": avg_memory,
                    "maximum_memory": avg_memory + 0.025 + (interval % 2) * 0.004,
                    "assigned_memory": request_memory,
                }
            )
    frame = pd.DataFrame(rows)
    numeric = frame.select_dtypes(include=[np.number]).columns
    frame[numeric] = frame[numeric].round(8)
    return assign_chronological_splits(frame)


def write_synthetic_fixture(directory: str | Path) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    data_path = directory / "synthetic_workloads.parquet"
    manifest_path = directory / "synthetic_manifest.json"
    synthetic_frame().to_parquet(data_path, index=False, compression="zstd")
    return write_manifest(
        data_path,
        manifest_path,
        source="deterministic synthetic fixture; not research evidence",
        cell="fixture",
        selection_rule="four generated tasks with 36 five-minute intervals",
        dataset_name="synthetic",
    )
