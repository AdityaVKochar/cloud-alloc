from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select, text

from .extensions import db
from .models import Task, WorkloadSample


api = Blueprint("api", __name__)


@api.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db.session.rollback()
        return jsonify(status="unhealthy", database="unavailable"), 503
    return jsonify(status="ok", database="available", milestone="30-percent-foundation")


def _optional_int(name: str):
    raw = request.args.get(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer trace timestamp") from exc


@api.get("/workloads/summary")
def workload_summary():
    try:
        start, end = _optional_int("start"), _optional_int("end")
    except ValueError as exc:
        return jsonify(error="validation_error", message=str(exc)), 400
    if start is not None and end is not None and start > end:
        return jsonify(error="validation_error", message="start must not be greater than end"), 400

    filters = []
    if start is not None:
        filters.append(WorkloadSample.start_time >= start)
    if end is not None:
        filters.append(WorkloadSample.start_time <= end)
    summary = db.session.execute(
        select(
            func.count(WorkloadSample.id),
            func.count(func.distinct(WorkloadSample.task_id)),
            func.min(WorkloadSample.start_time),
            func.max(WorkloadSample.end_time),
            func.avg(WorkloadSample.average_cpu),
            func.avg(WorkloadSample.maximum_cpu),
            func.avg(WorkloadSample.average_memory),
            func.avg(WorkloadSample.maximum_memory),
            func.avg(WorkloadSample.request_cpu),
            func.avg(WorkloadSample.request_memory),
        ).where(*filters)
    ).one()
    return jsonify(
        units="normalized_resource_capacity",
        sample_count=int(summary[0] or 0),
        task_count=int(summary[1] or 0),
        start_time=summary[2],
        end_time=summary[3],
        averages={
            "cpu_usage": summary[4],
            "cpu_maximum": summary[5],
            "memory_usage": summary[6],
            "memory_maximum": summary[7],
            "cpu_request": summary[8],
            "memory_request": summary[9],
        },
    )

