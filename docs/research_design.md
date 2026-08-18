# Research design

## Problem definition

Cloud task CPU and memory requirements change over time. Static requests can waste capacity, while delayed reactive changes can expose tasks to resource shortages. This project investigates whether one-step-ahead workload forecasts can drive better allocation recommendations than static requests and threshold-based reactive scaling.

The implementation uses Google Cluster Trace 2019 because its `instance_usage` records contain CPU and memory usage and its `instance_events` records contain requested resources. The data is sampled because the full trace is approximately 2.4 TiB compressed.

## Aim and objectives

The aim is to build and evaluate a reproducible system that predicts the maximum normalized CPU and memory demand of a cloud task for the next five-minute interval and converts the prediction into an allocation recommendation.

Objectives:

1. Construct a deterministic, laptop-sized trace sample without temporal leakage.
2. Characterize CPU/memory usage, requests, missingness, and temporal variation.
3. Establish persistence and rolling baselines before fitting machine-learning models.
4. Compare Ridge, random forest, and histogram gradient boosting in later work.
5. Compare static, reactive, predictive, and oracle allocations on the same test rows in later work.
6. Persist workloads, experiments, predictions, decisions, and metrics in a relational database.
7. Expose reproducible results through a backend and dashboard.

## Research questions and hypotheses

1. How accurately can maximum CPU and memory demand one interval ahead be predicted from the previous hour?
2. Does predictive allocation reduce waste relative to static requests?
3. Does it reduce under-provisioning relative to delayed reactive scaling?
4. Does the most accurate forecasting model also give the best allocation result?

The hypotheses are that predictive allocation reduces static waste, reduces reactive under-provisioning, and that forecast-error ranking does not always equal allocation-outcome ranking.

## Dataset method

- Source: Google Cluster Trace 2019, cell `a`.
- Unit of analysis: one task instance identified by `(cell, collection_id, instance_index)`.
- Window: a fixed contiguous seven-day period.
- Cohort: at most 1,000 tasks selected by a stable SHA-256 hash, each with at least 80% of expected intervals.
- Interval: five minutes, represented in trace-relative microseconds.
- Measures: average/maximum CPU and memory usage, requested CPU/memory, assigned memory, scheduling class, and priority.
- One missing interval is forward-filled from the previous observation. Longer gaps remain discontinuities and cannot form forecast pairs.
- Global time cutoffs assign 60% train, 20% validation, and 20% test data. All preprocessing parameters learned later must be fitted using train/validation only.

The normalized extract is stored as Parquet with a checksum manifest. No interpretation in vCPU or GB is permitted because public trace values are normalized.

## Current baseline method

For a task observed in interval `t`, the persistence baseline predicts that its maximum CPU and maximum memory in `t+1` equal their observed maxima in `t`. Pairs are retained only when timestamps differ by exactly five minutes. MAE, RMSE, sMAPE, and R² are calculated on the validation split. The test split remains unreported until final evaluation.

## Later allocation evaluation

Later milestones will compare static request, threshold-reactive, predictive-plus-safety-buffer, and oracle policies. Primary measures will be waste ratio, deficit ratio, deficit event rate, useful utilization, allocation churn, and task-level bootstrap confidence intervals. These results do not exist at the 30% milestone.

## Ethical, validity, and reproducibility considerations

- Trace identifiers are obfuscated; the project makes no attempt to identify users or workloads.
- Long-running-task and single-cell sampling limits generalizability and must be reported.
- Stable-task filtering introduces survivorship bias.
- Missing data and normalized units restrict interpretation.
- A prediction improvement is not assumed to imply an allocation improvement.
- Negative results are valid when methods and comparisons are reproducible.
- Synthetic fixture results demonstrate software behavior only and may never be reported as empirical cloud findings.
