from __future__ import annotations

from collections import defaultdict

import pandas as pd
from sqlalchemy import insert, select

from .extensions import db
from .models import Task, WorkloadSample


def _chunks(items: list[dict], size: int = 5000):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def ingest_frame(frame: pd.DataFrame) -> dict[str, int]:
    task_columns = ["cell", "collection_id", "instance_index", "scheduling_class", "priority"]
    tasks = frame[task_columns].drop_duplicates(["cell", "collection_id", "instance_index"])
    existing = {
        (task.cell, task.collection_id, task.instance_index): task.id
        for task in db.session.scalars(select(Task)).all()
    }
    created_tasks = 0
    for row in tasks.itertuples(index=False):
        key = (row.cell, int(row.collection_id), int(row.instance_index))
        if key not in existing:
            task = Task(
                cell=row.cell,
                collection_id=int(row.collection_id),
                instance_index=int(row.instance_index),
                scheduling_class=None if pd.isna(row.scheduling_class) else int(row.scheduling_class),
                priority=None if pd.isna(row.priority) else int(row.priority),
            )
            db.session.add(task)
            db.session.flush()
            existing[key] = task.id
            created_tasks += 1

    by_task: dict[int, list[dict]] = defaultdict(list)
    for row in frame.itertuples(index=False):
        task_id = existing[(row.cell, int(row.collection_id), int(row.instance_index))]
        by_task[task_id].append(
            {
                "task_id": task_id,
                "start_time": int(row.start_time),
                "end_time": int(row.end_time),
                "request_cpu": None if pd.isna(row.request_cpu) else float(row.request_cpu),
                "request_memory": None if pd.isna(row.request_memory) else float(row.request_memory),
                "average_cpu": float(row.average_cpu),
                "maximum_cpu": float(row.maximum_cpu),
                "average_memory": float(row.average_memory),
                "maximum_memory": float(row.maximum_memory),
                "assigned_memory": None if pd.isna(row.assigned_memory) else float(row.assigned_memory),
                "split": row.split,
            }
        )

    inserted_samples = 0
    for task_id, rows in by_task.items():
        starts = [item["start_time"] for item in rows]
        known = set(
            db.session.scalars(
                select(WorkloadSample.start_time).where(
                    WorkloadSample.task_id == task_id,
                    WorkloadSample.start_time >= min(starts),
                    WorkloadSample.start_time <= max(starts),
                )
            ).all()
        )
        new_rows = [item for item in rows if item["start_time"] not in known]
        for chunk in _chunks(new_rows):
            db.session.execute(insert(WorkloadSample), chunk)
        inserted_samples += len(new_rows)
    db.session.commit()
    return {"tasks_created": created_tasks, "samples_inserted": inserted_samples}
