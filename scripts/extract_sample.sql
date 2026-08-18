-- Optional BigQuery extraction path for Google Cluster Trace 2019 cell a.
-- Prefer the streaming JSON.GZ preprocessor when BigQuery billing is unavailable.
-- Query cost must be reviewed in the BigQuery UI before execution.

DECLARE window_start INT64 DEFAULT 0;
DECLARE window_end INT64 DEFAULT 7 * 24 * 60 * 60 * 1000000;

WITH eligible AS (
  SELECT collection_id, instance_index
  FROM `google.com:google-cluster-data.clusterdata_2019_a.instance_usage`
  WHERE start_time >= window_start AND start_time < window_end
    AND MOD(ABS(FARM_FINGERPRINT(CONCAT(CAST(collection_id AS STRING), ':', CAST(instance_index AS STRING)))), 50) = 0
  GROUP BY collection_id, instance_index
  HAVING COUNT(DISTINCT start_time) >= CAST(7 * 24 * 12 * 0.80 AS INT64)
  ORDER BY FARM_FINGERPRINT(CONCAT(CAST(collection_id AS STRING), ':', CAST(instance_index AS STRING)))
  LIMIT 1000
), usage_rows AS (
  SELECT u.*
  FROM `google.com:google-cluster-data.clusterdata_2019_a.instance_usage` u
  JOIN eligible e USING (collection_id, instance_index)
  WHERE u.start_time >= window_start AND u.start_time < window_end
), joined AS (
  SELECT
    'a' AS cell,
    u.collection_id,
    u.instance_index,
    u.start_time,
    u.end_time,
    e.scheduling_class,
    e.priority,
    e.resource_request.cpus AS request_cpu,
    e.resource_request.memory AS request_memory,
    u.average_usage.cpus AS average_cpu,
    u.maximum_usage.cpus AS maximum_cpu,
    u.average_usage.memory AS average_memory,
    u.maximum_usage.memory AS maximum_memory,
    u.assigned_memory,
    ROW_NUMBER() OVER (
      PARTITION BY u.collection_id, u.instance_index, u.start_time
      ORDER BY e.time DESC
    ) AS request_rank
  FROM usage_rows u
  LEFT JOIN `google.com:google-cluster-data.clusterdata_2019_a.instance_events` e
    ON e.collection_id = u.collection_id
   AND e.instance_index = u.instance_index
   AND e.time <= u.start_time
)
SELECT * EXCEPT(request_rank)
FROM joined
WHERE request_rank = 1;

