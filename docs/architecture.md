# Architecture and experiment flows

## System architecture

```mermaid
flowchart LR
    G["Google 2019 JSON.GZ shards"] --> P["Streaming preprocessor"]
    P --> Q["Validated Parquet sample"]
    P --> M["Checksum manifest"]
    Q --> I["Idempotent ingestion"]
    M --> I
    I --> DB[("PostgreSQL")]
    DB --> E["EDA generator"]
    DB --> B["Persistence baseline"]
    DB --> API["Flask read API"]
    E --> R["JSON and Plotly reports"]
    B --> DB
```

Green-path scope at 30% is represented by every component above. Advanced models, allocation simulation, recommendation endpoints, and the analytics dashboard are later components and are not silently mocked.

## Data flow and leakage boundary

```mermaid
flowchart TD
    U["Usage records"] --> V["Validate finite, non-negative values"]
    X["Resource-request events"] --> J["Join latest event available at sample time"]
    V --> J
    J --> C["Coverage and stable-hash cohort selection"]
    C --> F["Past-only single-gap forward fill"]
    F --> S["Global chronological 60/20/20 split"]
    S --> T["Observation at t"]
    T -->|"exactly +5 minutes"| Y["Target at t+1"]
```

An event is joined only when its event time is no later than the workload sample. Persistence prediction uses the current maximum only, and forecast pairs cannot cross a long gap.

## Entity relationship diagram

```mermaid
erDiagram
    TASKS ||--o{ WORKLOAD_SAMPLES : contains
    TASKS ||--o{ PREDICTIONS : receives
    TASKS ||--o{ ALLOCATION_DECISIONS : receives
    EXPERIMENTS ||--o{ PREDICTIONS : produces
    EXPERIMENTS ||--o{ ALLOCATION_DECISIONS : evaluates
    EXPERIMENTS ||--o{ EVALUATION_METRICS : summarizes

    TASKS {
      int id PK
      string cell
      bigint collection_id
      bigint instance_index
    }
    WORKLOAD_SAMPLES {
      int id PK
      int task_id FK
      bigint start_time
      float maximum_cpu
      float maximum_memory
      string split
    }
    EXPERIMENTS {
      int id PK
      string model_type
      string dataset_version
      string status
    }
    PREDICTIONS {
      int id PK
      int experiment_id FK
      int task_id FK
      bigint target_time
    }
    ALLOCATION_DECISIONS {
      int id PK
      int experiment_id FK
      string policy
      float allocated_cpu
      float allocated_memory
    }
    EVALUATION_METRICS {
      int id PK
      int experiment_id FK
      string resource
      string metric_name
      float metric_value
    }
```

The allocation tables are scaffolded now so later migrations do not disrupt stored baseline experiments; they remain empty at 30%.

## Full experiment flow planned after 30%

```mermaid
flowchart LR
    D["Frozen splits"] --> FE["Lag and rolling features"]
    FE --> ML["Classical regressors"]
    ML --> VP["Validation predictions"]
    VP --> SB["Residual safety buffer"]
    ML --> TP["Untouched test predictions"]
    TP --> PS["Policy simulator"]
    SB --> PS
    PS --> CM["Waste, deficit, utilization, churn"]
```

