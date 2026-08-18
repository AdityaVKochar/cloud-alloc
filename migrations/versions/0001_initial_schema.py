"""Initial CloudAlloc research schema.

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cell", sa.String(8), nullable=False),
        sa.Column("collection_id", sa.BigInteger(), nullable=False),
        sa.Column("instance_index", sa.BigInteger(), nullable=False),
        sa.Column("scheduling_class", sa.Integer()),
        sa.Column("priority", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("cell", "collection_id", "instance_index", name="uq_task_trace_id"),
    )
    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("model_type", sa.String(64), nullable=False),
        sa.Column("dataset_version", sa.String(128), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("artifact_path", sa.Text()),
        sa.Column("validation_summary", sa.JSON()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_experiment_status", "experiments", ["status"])
    op.create_table(
        "workload_samples",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_time", sa.BigInteger(), nullable=False),
        sa.Column("end_time", sa.BigInteger(), nullable=False),
        sa.Column("request_cpu", sa.Float()),
        sa.Column("request_memory", sa.Float()),
        sa.Column("average_cpu", sa.Float(), nullable=False),
        sa.Column("maximum_cpu", sa.Float(), nullable=False),
        sa.Column("average_memory", sa.Float(), nullable=False),
        sa.Column("maximum_memory", sa.Float(), nullable=False),
        sa.Column("assigned_memory", sa.Float()),
        sa.Column("split", sa.String(16)),
        sa.UniqueConstraint("task_id", "start_time", name="uq_sample_task_time"),
    )
    op.create_index("ix_workload_samples_start_time", "workload_samples", ["start_time"])
    op.create_index("ix_workload_samples_task_time", "workload_samples", ["task_id", "start_time"])
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_time", sa.BigInteger(), nullable=False),
        sa.Column("split", sa.String(16), nullable=False),
        sa.Column("predicted_cpu", sa.Float(), nullable=False),
        sa.Column("predicted_memory", sa.Float(), nullable=False),
        sa.Column("actual_cpu", sa.Float(), nullable=False),
        sa.Column("actual_memory", sa.Float(), nullable=False),
        sa.Column("average_cpu", sa.Float(), nullable=False),
        sa.Column("average_memory", sa.Float(), nullable=False),
        sa.UniqueConstraint("experiment_id", "task_id", "target_time", name="uq_prediction"),
    )
    op.create_index("ix_prediction_experiment", "predictions", ["experiment_id"])
    op.create_table(
        "allocation_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_time", sa.BigInteger(), nullable=False),
        sa.Column("policy", sa.String(32), nullable=False),
        sa.Column("allocated_cpu", sa.Float(), nullable=False),
        sa.Column("allocated_memory", sa.Float(), nullable=False),
        sa.Column("cpu_waste", sa.Float(), nullable=False),
        sa.Column("memory_waste", sa.Float(), nullable=False),
        sa.Column("cpu_deficit", sa.Float(), nullable=False),
        sa.Column("memory_deficit", sa.Float(), nullable=False),
        sa.UniqueConstraint("experiment_id", "task_id", "target_time", "policy", name="uq_allocation"),
    )
    op.create_index("ix_allocation_experiment_policy", "allocation_decisions", ["experiment_id", "policy"])
    op.create_table(
        "evaluation_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy", sa.String(32), nullable=False),
        sa.Column("resource", sa.String(16), nullable=False),
        sa.Column("split", sa.String(16), nullable=False),
        sa.Column("metric_name", sa.String(64), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("ci_low", sa.Float()),
        sa.Column("ci_high", sa.Float()),
        sa.Column("deficit_weight", sa.Integer(), nullable=False),
        sa.UniqueConstraint("experiment_id", "policy", "resource", "split", "metric_name", "deficit_weight", name="uq_metric"),
    )
    op.create_index("ix_metric_lookup", "evaluation_metrics", ["experiment_id", "resource", "policy"])


def downgrade():
    op.drop_table("evaluation_metrics")
    op.drop_table("allocation_decisions")
    op.drop_table("predictions")
    op.drop_table("workload_samples")
    op.drop_table("experiments")
    op.drop_table("tasks")

