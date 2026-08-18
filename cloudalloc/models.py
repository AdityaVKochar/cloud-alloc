from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Task(db.Model):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("cell", "collection_id", "instance_index", name="uq_task_trace_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cell: Mapped[str] = mapped_column(String(8), nullable=False)
    collection_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    instance_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    scheduling_class: Mapped[int | None] = mapped_column(Integer)
    priority: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    samples: Mapped[list["WorkloadSample"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class WorkloadSample(db.Model):
    __tablename__ = "workload_samples"
    __table_args__ = (
        UniqueConstraint("task_id", "start_time", name="uq_sample_task_time"),
        Index("ix_workload_samples_start_time", "start_time"),
        Index("ix_workload_samples_task_time", "task_id", "start_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    request_cpu: Mapped[float | None] = mapped_column(Float)
    request_memory: Mapped[float | None] = mapped_column(Float)
    average_cpu: Mapped[float] = mapped_column(Float, nullable=False)
    maximum_cpu: Mapped[float] = mapped_column(Float, nullable=False)
    average_memory: Mapped[float] = mapped_column(Float, nullable=False)
    maximum_memory: Mapped[float] = mapped_column(Float, nullable=False)
    assigned_memory: Mapped[float | None] = mapped_column(Float)
    split: Mapped[str | None] = mapped_column(String(16))

    task: Mapped[Task] = relationship(back_populates="samples")


class Experiment(db.Model):
    __tablename__ = "experiments"
    __table_args__ = (Index("ix_experiment_status", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(128), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(Text)
    validation_summary: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )


class Prediction(db.Model):
    __tablename__ = "predictions"
    __table_args__ = (
        UniqueConstraint("experiment_id", "task_id", "target_time", name="uq_prediction"),
        Index("ix_prediction_experiment", "experiment_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    target_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    split: Mapped[str] = mapped_column(String(16), nullable=False)
    predicted_cpu: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_memory: Mapped[float] = mapped_column(Float, nullable=False)
    actual_cpu: Mapped[float] = mapped_column(Float, nullable=False)
    actual_memory: Mapped[float] = mapped_column(Float, nullable=False)
    average_cpu: Mapped[float] = mapped_column(Float, nullable=False)
    average_memory: Mapped[float] = mapped_column(Float, nullable=False)

    experiment: Mapped[Experiment] = relationship(back_populates="predictions")


class AllocationDecision(db.Model):
    __tablename__ = "allocation_decisions"
    __table_args__ = (
        UniqueConstraint("experiment_id", "task_id", "target_time", "policy", name="uq_allocation"),
        Index("ix_allocation_experiment_policy", "experiment_id", "policy"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    target_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    policy: Mapped[str] = mapped_column(String(32), nullable=False)
    allocated_cpu: Mapped[float] = mapped_column(Float, nullable=False)
    allocated_memory: Mapped[float] = mapped_column(Float, nullable=False)
    cpu_waste: Mapped[float] = mapped_column(Float, nullable=False)
    memory_waste: Mapped[float] = mapped_column(Float, nullable=False)
    cpu_deficit: Mapped[float] = mapped_column(Float, nullable=False)
    memory_deficit: Mapped[float] = mapped_column(Float, nullable=False)


class EvaluationMetric(db.Model):
    __tablename__ = "evaluation_metrics"
    __table_args__ = (
        UniqueConstraint(
            "experiment_id", "policy", "resource", "split", "metric_name", "deficit_weight",
            name="uq_metric",
        ),
        Index("ix_metric_lookup", "experiment_id", "resource", "policy"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    policy: Mapped[str] = mapped_column(String(32), default="forecast", nullable=False)
    resource: Mapped[str] = mapped_column(String(16), nullable=False)
    split: Mapped[str] = mapped_column(String(16), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    ci_low: Mapped[float | None] = mapped_column(Float)
    ci_high: Mapped[float | None] = mapped_column(Float)
    deficit_weight: Mapped[int] = mapped_column(Integer, default=4, nullable=False)

