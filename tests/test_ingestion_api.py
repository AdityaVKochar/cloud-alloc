from __future__ import annotations

from cloudalloc.extensions import db
from cloudalloc.ingestion import ingest_frame
from cloudalloc.models import Task, WorkloadSample
from cloudalloc.sample_data import synthetic_frame


def test_ingestion_is_idempotent(app):
    with app.app_context():
        frame = synthetic_frame(task_count=2, intervals=20)
        first = ingest_frame(frame)
        second = ingest_frame(frame)
        assert first == {"tasks_created": 2, "samples_inserted": len(frame)}
        assert second == {"tasks_created": 0, "samples_inserted": 0}
        assert db.session.query(Task).count() == 2
        assert db.session.query(WorkloadSample).count() == len(frame)


def test_health_and_summary_integration(app, client):
    with app.app_context():
        ingest_frame(synthetic_frame(task_count=3, intervals=18))
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.get_json()["database"] == "available"

    response = client.get("/api/workloads/summary")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["task_count"] == 3
    assert payload["sample_count"] > 0
    assert payload["units"] == "normalized_resource_capacity"


def test_summary_validates_trace_range(client):
    response = client.get("/api/workloads/summary?start=bad")
    assert response.status_code == 400
    assert response.get_json()["error"] == "validation_error"
    response = client.get("/api/workloads/summary?start=20&end=10")
    assert response.status_code == 400

