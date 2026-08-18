INTERVAL_MICROSECONDS = 300_000_000
REQUIRED_COLUMNS = [
    "cell",
    "collection_id",
    "instance_index",
    "start_time",
    "end_time",
    "scheduling_class",
    "priority",
    "request_cpu",
    "request_memory",
    "average_cpu",
    "maximum_cpu",
    "average_memory",
    "maximum_memory",
    "assigned_memory",
]

MODEL_NAMES = ("persistence", "rolling_mean", "ridge", "random_forest", "hist_gradient_boosting")
RESOURCES = ("cpu", "memory")
POLICIES = ("static", "reactive", "predictive", "oracle")

