from __future__ import annotations

import json
from pathlib import Path

import click
from flask import Flask

from .analysis import build_eda
from .baseline import run_persistence_baseline
from .extensions import db
from .ingestion import ingest_frame
from .preprocessing import load_manifest, prepare_google_trace, write_manifest
from .sample_data import write_synthetic_fixture


def register_cli(app: Flask) -> None:
    app.cli.add_command(data_group)
    app.cli.add_command(baseline_group)
    app.cli.add_command(analysis_group)
    app.cli.add_command(demo_group)


@click.group("data")
def data_group():
    """Prepare and ingest normalized workload datasets."""


@data_group.command("prepare")
@click.option("--usage", "usage_paths", type=click.Path(exists=True, path_type=Path), multiple=True, required=True)
@click.option("--events", "event_paths", type=click.Path(exists=True, path_type=Path), multiple=True, required=True)
@click.option("--output", type=click.Path(path_type=Path), required=True)
@click.option("--manifest", "manifest_path", type=click.Path(path_type=Path), required=True)
@click.option("--cell", default="a", show_default=True)
@click.option("--start-time", default=0, type=int, show_default=True)
@click.option("--days", default=7, type=click.IntRange(1), show_default=True)
@click.option("--max-tasks", default=1000, type=click.IntRange(1), show_default=True)
@click.option("--minimum-coverage", default=0.80, type=click.FloatRange(0.01, 1.0), show_default=True)
@click.option("--candidate-modulus", default=50, type=click.IntRange(1), show_default=True)
def prepare_command(usage_paths, event_paths, output, manifest_path, cell, start_time, days, max_tasks, minimum_coverage, candidate_modulus):
    output = prepare_google_trace(
        usage_paths, event_paths, output, cell=cell, start_time=start_time, days=days,
        max_tasks=max_tasks, minimum_coverage=minimum_coverage, candidate_modulus=candidate_modulus,
    )
    manifest = write_manifest(
        output, manifest_path,
        source="Google Cluster Trace 2019 official instance_usage and instance_events JSONL shards",
        cell=cell,
        selection_rule=f"{days} days; <= {max_tasks} tasks; >= {minimum_coverage:.0%} coverage; sha256 hash modulo {candidate_modulus}",
    )
    click.echo(str(manifest))


@data_group.command("ingest")
@click.argument("manifest", type=click.Path(exists=True, path_type=Path))
def ingest_command(manifest):
    metadata, frame = load_manifest(manifest)
    result = ingest_frame(frame)
    click.echo(json.dumps({**result, "dataset_version": metadata["dataset_version"]}, indent=2))


@click.group("baseline")
def baseline_group():
    """Run the 30% milestone persistence baseline."""


@baseline_group.command("run")
@click.option("--dataset-version", required=True)
@click.option("--output", default="reports/generated/persistence_baseline.json", type=click.Path(path_type=Path))
@click.option("--include-test", is_flag=True, help="Final-milestone only: evaluate the frozen test split.")
def baseline_command(dataset_version, output, include_test):
    experiment, report = run_persistence_baseline(dataset_version, output, include_test=include_test)
    click.echo(json.dumps({"experiment_id": experiment.id, **report}, indent=2))


@click.group("analysis")
def analysis_group():
    """Generate exploratory analysis artifacts."""


@analysis_group.command("eda")
@click.option("--output", default="reports/generated", type=click.Path(path_type=Path))
@click.option("--split", type=click.Choice(["train", "validation", "test", "all"]), default="train", show_default=True)
def eda_command(output, split):
    stats = build_eda(output, split=split)
    click.echo(json.dumps(stats["scope"], indent=2))


@click.group("demo")
def demo_group():
    """Manage the deterministic, non-research demonstration fixture."""


@demo_group.command("seed")
@click.option("--directory", default="data/fixtures", type=click.Path(path_type=Path))
def seed_command(directory):
    db.create_all()
    manifest_path = write_synthetic_fixture(directory)
    metadata, frame = load_manifest(manifest_path)
    result = ingest_frame(frame)
    click.echo(json.dumps({**result, "manifest": str(manifest_path), "dataset_version": metadata["dataset_version"]}, indent=2))
