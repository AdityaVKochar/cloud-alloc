# CloudAlloc: predictive cloud resource allocation

CloudAlloc is a research prototype for studying next-interval CPU and memory demand in Google Cluster Trace 2019. This repository currently implements the **30% foundation milestone only**: reproducible preprocessing, a normalized database, EDA, a leakage-free persistence baseline, two read-only API endpoints, tests, and research documentation.

Advanced regressors, allocation-policy simulation, recommendation endpoints, and the final analytics dashboard are intentionally not implemented yet.

## What is implemented

- Streaming normalization of official `instance_usage` and `instance_events` JSON/JSON.GZ shards.
- Stable SHA-256 task sampling, seven-day filtering, 80% coverage filtering, and one-gap forward fill.
- Chronological 60/20/20 train/validation/test labels.
- Versioned Parquet output and checksum-protected manifest.
- PostgreSQL schema with Alembic migrations; SQLite works for tests and a no-server demonstration.
- Idempotent task and workload ingestion.
- CPU/memory EDA as JSON and an interactive Plotly HTML report.
- Persistence forecast: the current maximum predicts the next five-minute maximum.
- `GET /api/health` and `GET /api/workloads/summary`.

All CPU and memory values remain in **normalized resource-capacity units**. They must not be presented as physical vCPUs or GB.

## Quick start with PostgreSQL

Requirements: Python 3.11+, Docker Desktop (or an existing PostgreSQL instance), and enough disk for the selected trace shards.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
docker compose up -d postgres
$env:FLASK_APP = "wsgi.py"
$env:DATABASE_URL = "postgresql+psycopg://cloudalloc:cloudalloc@localhost:5432/cloudalloc"
python -m flask db upgrade
```

For a fast local demonstration without PostgreSQL:

```powershell
$env:FLASK_APP = "wsgi.py"
$env:DATABASE_URL = "sqlite:///cloudalloc-demo.sqlite3"
python -m flask demo seed
python -m flask analysis eda
python -m flask baseline run --dataset-version synthetic-fixture
python -m flask run
```

The generated synthetic outputs prove the pipeline works; they are not research evidence.

## Prepare and ingest Google trace data

Download only the official `instance_usage` and `instance_events` shards that cover the desired window. Individual compressed shards can be hundreds of megabytes. Do not attempt to download the complete trace on a laptop.

```powershell
python -m flask data prepare `
  --usage data/raw/instance_usage-000000000000.json.gz `
  --events data/raw/instance_events-000000000000.json.gz `
  --output data/processed/google_a_7d.parquet `
  --manifest data/processed/google_a_7d.manifest.json `
  --cell a --start-time 0 --days 7 --max-tasks 1000 `
  --minimum-coverage 0.80 --candidate-modulus 50

python -m flask data ingest data/processed/google_a_7d.manifest.json
python -m flask analysis eda --output reports/generated
python -m flask baseline run --dataset-version <version-from-ingest-output>
```

If too few tasks meet coverage, include more usage shards or reduce `--candidate-modulus`. Decreasing the modulus admits more hash buckets and uses more memory.

## API

- `GET /api/health` verifies application/database availability.
- `GET /api/workloads/summary` reports task/sample counts, trace range, and average requests/usages.
- `GET /api/workloads/summary?start=0&end=3600000000` restricts the summary to a trace-time range.

Errors use JSON with `error` and `message` fields. Trace timestamps are integer microseconds relative to the trace, not wall-clock dates.

## Reproducibility and safeguards

- The manifest records source, selection rule, schema version, trace range, row/task counts, units, and the Parquet SHA-256.
- Ingestion verifies the checksum and is idempotent under the database uniqueness constraints.
- Splits are chronological across the selected window.
- The persistence forecast pairs only exactly adjacent five-minute intervals and never crosses a gap.
- EDA defaults to the training split, and the 30% baseline reports validation metrics only; `--include-test` is reserved for final evaluation.
- Raw data, prepared extracts, model artifacts, and generated reports are excluded from version control.
- The test fixture is generated deterministically by `python -m flask demo seed`.

Run verification with:

```powershell
python -m pytest
```

See [research design](docs/research_design.md), [literature matrix](docs/literature_matrix.md), [architecture](docs/architecture.md), and the [30% progress report](reports/30_percent_progress.md).
