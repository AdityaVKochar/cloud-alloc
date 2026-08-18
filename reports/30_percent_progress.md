# 30% milestone progress report

## Status

The research and software foundation is implemented. The repository contains the normalized data contract, deterministic trace preprocessor, checksum manifest, relational schema and migration, idempotent ingestion, EDA generator, leakage-safe persistence baseline, health/summary APIs, fixture, tests, architecture diagrams, methodology, and literature matrix.

This milestone does **not** claim that predictive allocation reduces waste or under-provisioning. Advanced machine-learning models, policy simulation, confidence intervals, recommendation endpoints, and the final dashboard are future work.

## Completed deliverables

- Final problem definition, aim, objectives, research questions, hypotheses, methods, limitations, and metric plan.
- Thirteen-study literature matrix recording datasets, methods, and whether allocation outcomes were evaluated.
- System architecture, data flow, leakage boundary, ER diagram, and planned experiment flow.
- Flask application scaffold and PostgreSQL/Alembic schema for all planned entities.
- Streaming Google JSONL/GZIP normalization with stable task hashing and time/coverage limits.
- Required-column, type, range, timestamp, checksum, and row-count validation.
- Past-only single-gap filling and chronological 60/20/20 split assignment.
- Idempotent workload ingestion.
- Reproducible JSON and Plotly EDA outputs.
- Persistence baseline for CPU and memory with MAE, RMSE, sMAPE, and R².
- `GET /api/health` and `GET /api/workloads/summary` with validation.
- Deterministic synthetic fixture and automated unit/integration tests.

## Preliminary observations

The fixture demonstrates that the pipeline detects request-versus-usage gaps, computes temporal summaries, and produces next-interval predictions. Fixture statistics are deliberately not reported here: generated data is not valid evidence about production cloud workloads.

Empirical observations and baseline values must be inserted only after the official Google sample is prepared and its manifest/checksum are archived.

## Reproducibility evidence

1. A fresh database is created with `flask db upgrade`.
2. `python -m flask demo seed` creates and idempotently loads the fixture.
3. Re-running the seed inserts zero duplicate samples.
4. `python -m flask analysis eda` regenerates JSON and HTML outputs from training records by default.
5. `python -m flask baseline run` pairs only exactly adjacent intervals and reports validation metrics only.
6. `pytest` checks validation, gap handling, ingestion, APIs, and baseline behavior.

## Current risks and controls

| Risk | Control |
|---|---|
| Official trace size exceeds laptop resources | Stream compressed shards, hash-filter early, cap tasks, and store a Parquet extract. |
| Too few complete tasks in downloaded shards | Add adjacent shards or reduce the configurable hash modulus. |
| Requests are missing before the chosen window | Preserve nulls, report missingness, and do not invent resource-request values. |
| Temporal leakage | Join only prior events, forward-fill from the past, split chronologically, and require exact adjacent forecast intervals. |
| Single-cell/long-task bias | Record selection in the manifest and state it as a validity limitation. |
| Normalized units misrepresented | Label database/API/report values as normalized capacity, never vCPU or GB. |

## Remaining 70%

- 30–50%: lag/rolling feature pipeline and Ridge, random forest, and histogram-gradient-boosting experiments.
- 50–70%: static, reactive, predictive, and oracle allocation simulation and statistical comparison.
- 70–85%: experiment/comparison/recommendation APIs and analytics dashboard.
- 85–100%: frozen-test evaluation, robustness checks, final report, presentation, and demonstration.
