from __future__ import annotations

import gzip
import hashlib
import json
import math
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import pandas as pd

from .constants import INTERVAL_MICROSECONDS, REQUIRED_COLUMNS


SCHEMA_VERSION = "cloudalloc-normalized-v1"


class DataValidationError(ValueError):
    """Raised when a prepared workload file violates the normalized schema."""


def stable_task_hash(collection_id: int, instance_index: int) -> int:
    value = f"{collection_id}:{instance_index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(value).digest()[:8], "big")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _open_jsonl(path: str | Path):
    path = Path(path)
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("r", encoding="utf-8")


def _iter_jsonl(paths: Iterable[str | Path]) -> Iterator[dict]:
    for path in paths:
        with _open_jsonl(path) as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise DataValidationError(f"Invalid JSON in {path} at line {line_number}") from exc


def _number(value, default=np.nan) -> float:
    if value is None:
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _integer(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _usage_row(record: dict, cell: str) -> dict | None:
    average = record.get("average_usage") or {}
    maximum = record.get("maximum_usage") or {}
    collection_id = _integer(record.get("collection_id"))
    instance_index = _integer(record.get("instance_index"))
    start_time = _integer(record.get("start_time"))
    end_time = _integer(record.get("end_time"))
    if None in (collection_id, instance_index, start_time, end_time):
        return None
    return {
        "cell": cell,
        "collection_id": collection_id,
        "instance_index": instance_index,
        "start_time": start_time,
        "end_time": end_time,
        "average_cpu": _number(average.get("cpus")),
        "maximum_cpu": _number(maximum.get("cpus")),
        "average_memory": _number(average.get("memory")),
        "maximum_memory": _number(maximum.get("memory")),
        "assigned_memory": _number(record.get("assigned_memory")),
    }


def _event_row(record: dict) -> dict | None:
    request = record.get("resource_request") or {}
    collection_id = _integer(record.get("collection_id"))
    instance_index = _integer(record.get("instance_index"))
    event_time = _integer(record.get("time"))
    if None in (collection_id, instance_index, event_time):
        return None
    return {
        "collection_id": collection_id,
        "instance_index": instance_index,
        "time": event_time,
        "scheduling_class": _integer(record.get("scheduling_class")),
        "priority": _integer(record.get("priority")),
        "request_cpu": _number(request.get("cpus")),
        "request_memory": _number(request.get("memory")),
    }


def validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise DataValidationError(f"Missing required columns: {', '.join(missing)}")

    result = frame[REQUIRED_COLUMNS].copy()
    int_columns = ["collection_id", "instance_index", "start_time", "end_time"]
    numeric_columns = [
        *int_columns,
        "scheduling_class",
        "priority",
        "request_cpu",
        "request_memory",
        "average_cpu",
        "maximum_cpu",
        "average_memory",
        "maximum_memory",
        "assigned_memory",
    ]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    required_values = [
        "collection_id", "instance_index", "start_time", "end_time",
        "average_cpu", "maximum_cpu", "average_memory", "maximum_memory",
    ]
    if result[required_values].isna().any().any():
        bad = result[required_values].isna().sum()
        details = ", ".join(f"{name}={count}" for name, count in bad.items() if count)
        raise DataValidationError(f"Null or non-numeric required values: {details}")

    resources = ["request_cpu", "request_memory", "average_cpu", "maximum_cpu", "average_memory", "maximum_memory", "assigned_memory"]
    finite = np.isfinite(result[resources].fillna(0).to_numpy(dtype=float)).all()
    if not finite or (result[resources].fillna(0) < 0).any().any():
        raise DataValidationError("Resource values must be finite and non-negative")
    if (result["end_time"] <= result["start_time"]).any():
        raise DataValidationError("Every end_time must be greater than start_time")

    result[int_columns] = result[int_columns].astype("int64")
    result["cell"] = result["cell"].astype(str)
    result = result.sort_values(["collection_id", "instance_index", "start_time"])
    result = result.drop_duplicates(["cell", "collection_id", "instance_index", "start_time"], keep="last")
    return result.reset_index(drop=True)


def fill_single_interval_gaps(frame: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill exactly one missing five-minute interval using only past data."""
    additions: list[pd.Series] = []
    keys = ["cell", "collection_id", "instance_index"]
    for _, group in frame.groupby(keys, sort=False):
        group = group.sort_values("start_time")
        starts = group["start_time"].to_numpy()
        for index in np.where(np.diff(starts) == 2 * INTERVAL_MICROSECONDS)[0]:
            row = group.iloc[index].copy()
            row["start_time"] = int(starts[index] + INTERVAL_MICROSECONDS)
            row["end_time"] = int(row["start_time"] + INTERVAL_MICROSECONDS)
            additions.append(row)
    if additions:
        frame = pd.concat([frame, pd.DataFrame(additions)], ignore_index=True)
    return frame.sort_values(keys + ["start_time"]).reset_index(drop=True)


def assign_chronological_splits(frame: pd.DataFrame) -> pd.DataFrame:
    times = np.sort(frame["start_time"].unique())
    if len(times) < 5:
        raise DataValidationError("At least five distinct intervals are required for chronological splits")
    train_cutoff = times[max(0, math.ceil(len(times) * 0.60) - 1)]
    validation_cutoff = times[max(0, math.ceil(len(times) * 0.80) - 1)]
    result = frame.copy()
    result["split"] = np.select(
        [result["start_time"] <= train_cutoff, result["start_time"] <= validation_cutoff],
        ["train", "validation"],
        default="test",
    )
    return result


def prepare_google_trace(
    usage_paths: Iterable[str | Path],
    event_paths: Iterable[str | Path],
    output_path: str | Path,
    *,
    cell: str = "a",
    start_time: int = 0,
    days: int = 7,
    max_tasks: int = 1000,
    minimum_coverage: float = 0.80,
    candidate_modulus: int = 50,
) -> Path:
    """Stream official JSONL shards into a deterministic laptop-sized Parquet extract."""
    end_time = start_time + days * 24 * 60 * 60 * 1_000_000
    candidate_rows: list[dict] = []
    for record in _iter_jsonl(usage_paths):
        row = _usage_row(record, cell)
        if row is None or not (start_time <= row["start_time"] < end_time):
            continue
        key_hash = stable_task_hash(row["collection_id"], row["instance_index"])
        if key_hash % candidate_modulus == 0:
            candidate_rows.append(row)
    if not candidate_rows:
        raise DataValidationError("No candidate usage rows matched the time window and hash filter")

    usage = pd.DataFrame(candidate_rows)
    expected = days * 24 * 12
    counts = usage.groupby(["collection_id", "instance_index"])["start_time"].nunique()
    eligible = counts[counts >= math.ceil(expected * minimum_coverage)].index.tolist()
    eligible.sort(key=lambda key: stable_task_hash(*key))
    selected = set(eligible[:max_tasks])
    if not selected:
        raise DataValidationError(
            "No task met the coverage requirement; widen the input shards or lower candidate_modulus"
        )
    usage_index = pd.MultiIndex.from_frame(usage[["collection_id", "instance_index"]])
    usage = usage[usage_index.isin(selected)].copy()

    events: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for record in _iter_jsonl(event_paths):
        row = _event_row(record)
        if row and (row["collection_id"], row["instance_index"]) in selected:
            events[(row["collection_id"], row["instance_index"])].append(row)
    for rows in events.values():
        rows.sort(key=lambda item: item["time"])
    event_times = {key: [item["time"] for item in rows] for key, rows in events.items()}

    metadata = {name: [] for name in ("scheduling_class", "priority", "request_cpu", "request_memory")}
    for row in usage.itertuples(index=False):
        history = events.get((row.collection_id, row.instance_index), [])
        times = event_times.get((row.collection_id, row.instance_index), [])
        position = bisect_right(times, row.start_time) - 1
        event = history[position] if position >= 0 else {}
        for name in metadata:
            metadata[name].append(event.get(name, np.nan))
    for name, values in metadata.items():
        usage[name] = values

    usage = validate_frame(usage)
    usage = fill_single_interval_gaps(usage)
    usage = assign_chronological_splits(usage)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    usage.to_parquet(output, index=False, compression="zstd")
    return output


def write_manifest(
    data_path: str | Path,
    manifest_path: str | Path,
    *,
    source: str,
    cell: str,
    selection_rule: str,
    dataset_name: str = "google-2019",
) -> Path:
    data_path, manifest_path = Path(data_path).resolve(), Path(manifest_path).resolve()
    frame = pd.read_parquet(data_path)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "dataset_version": f"{dataset_name}-{cell}-{sha256_file(data_path)[:12]}",
        "source": source,
        "cell": cell,
        "data_file": str(Path(data_path).relative_to(manifest_path.parent)) if data_path.is_relative_to(manifest_path.parent) else str(data_path),
        "sha256": sha256_file(data_path),
        "row_count": int(len(frame)),
        "task_count": int(frame[["collection_id", "instance_index"]].drop_duplicates().shape[0]),
        "start_time": int(frame["start_time"].min()),
        "end_time": int(frame["end_time"].max()),
        "selection_rule": selection_rule,
        "units": "normalized resource capacity",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path


def load_manifest(manifest_path: str | Path) -> tuple[dict, pd.DataFrame]:
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required_manifest_fields = {
        "schema_version", "dataset_version", "source", "cell", "data_file", "sha256",
        "row_count", "task_count", "start_time", "end_time", "selection_rule", "units",
    }
    missing_fields = sorted(required_manifest_fields - set(manifest))
    if missing_fields:
        raise DataValidationError(f"Manifest is missing fields: {', '.join(missing_fields)}")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise DataValidationError(f"Unsupported schema_version: {manifest.get('schema_version')}")
    data_path = Path(manifest["data_file"])
    if not data_path.is_absolute():
        data_path = manifest_path.parent / data_path
    if not data_path.exists():
        raise DataValidationError(f"Prepared data file does not exist: {data_path}")
    if sha256_file(data_path) != manifest.get("sha256"):
        raise DataValidationError("Prepared data checksum does not match the manifest")
    raw_frame = pd.read_parquet(data_path)
    split_keys = ["cell", "collection_id", "instance_index", "start_time"]
    splits = raw_frame[split_keys + ["split"]].copy() if "split" in raw_frame.columns else None
    frame = validate_frame(raw_frame)
    if splits is None:
        frame = assign_chronological_splits(frame)
    else:
        frame = frame.merge(splits, on=split_keys, how="left", validate="one_to_one")
        if frame["split"].isna().any() or not set(frame["split"]).issubset({"train", "validation", "test"}):
            raise DataValidationError("Invalid chronological split labels in prepared data")
    if len(frame) != int(manifest.get("row_count", -1)):
        raise DataValidationError("Prepared data row count does not match the manifest")
    return manifest, frame
