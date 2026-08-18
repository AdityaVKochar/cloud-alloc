from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px

from .baseline import workload_frame


RESOURCE_COLUMNS = [
    "request_cpu", "request_memory", "average_cpu", "maximum_cpu",
    "average_memory", "maximum_memory",
]


def build_eda(output_directory: str | Path, split: str = "train") -> dict:
    frame = workload_frame()
    if frame.empty:
        raise ValueError("No workload samples are loaded")
    if split != "all":
        frame = frame[frame["split"] == split].copy()
        if frame.empty:
            raise ValueError(f"No workload samples are available for split '{split}'")
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    stats = {
        "scope": {
            "selected_split": split,
            "rows": int(len(frame)),
            "tasks": int(frame["task_id"].nunique()),
            "start_time": int(frame["start_time"].min()),
            "end_time": int(frame["start_time"].max()),
            "split_counts": {str(k): int(v) for k, v in frame["split"].value_counts().items()},
        },
        "descriptive_statistics": frame[RESOURCE_COLUMNS].describe().round(8).to_dict(),
        "missing_values": {name: int(value) for name, value in frame[RESOURCE_COLUMNS].isna().sum().items()},
        "correlations": frame[RESOURCE_COLUMNS].corr().round(6).to_dict(),
        "request_usage_gap": {
            "cpu_mean": float((frame["request_cpu"] - frame["average_cpu"]).mean()),
            "memory_mean": float((frame["request_memory"] - frame["average_memory"]).mean()),
            "cpu_request_below_max_rate": float((frame["request_cpu"] < frame["maximum_cpu"]).mean()),
            "memory_request_below_max_rate": float((frame["request_memory"] < frame["maximum_memory"]).mean()),
        },
        "warning": "Synthetic-fixture statistics are pipeline demonstrations, not research findings. Run on the Google sample for final EDA.",
    }
    (output_directory / "eda_summary.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")

    temporal = frame.groupby("start_time", as_index=False)[
        ["average_cpu", "maximum_cpu", "average_memory", "maximum_memory"]
    ].mean()
    figures = [
        px.histogram(frame, x="maximum_cpu", nbins=40, title="Maximum CPU distribution"),
        px.histogram(frame, x="maximum_memory", nbins=40, title="Maximum memory distribution"),
        px.line(temporal, x="start_time", y=["average_cpu", "maximum_cpu"], title="CPU usage over time"),
        px.line(temporal, x="start_time", y=["average_memory", "maximum_memory"], title="Memory usage over time"),
        px.scatter(frame, x="request_cpu", y="maximum_cpu", opacity=0.35, title="Requested versus maximum CPU"),
        px.scatter(frame, x="request_memory", y="maximum_memory", opacity=0.35, title="Requested versus maximum memory"),
    ]
    html = ["<!doctype html><html><head><meta charset='utf-8'><title>CloudAlloc EDA</title></head><body>"]
    html.append("<h1>Exploratory data analysis</h1><p>Values are normalized resource capacity.</p>")
    for index, figure in enumerate(figures):
        html.append(figure.to_html(full_html=False, include_plotlyjs="cdn" if index == 0 else False))
    html.append("</body></html>")
    (output_directory / "eda.html").write_text("\n".join(html), encoding="utf-8")
    return stats
