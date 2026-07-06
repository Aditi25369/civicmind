"""
BigQuery service — all analytics warehouse queries live here.
Each domain has its own dataset in BigQuery.
"""
import os
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET    = os.environ.get("BQ_DATASET", "civicmind_data")

_client: bigquery.Client = None


def get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=PROJECT_ID)
    return _client


def table(name: str) -> str:
    return f"`{PROJECT_ID}.{DATASET}.{name}`"


async def get_domain_summary(domain: str, days: int = 30) -> str:
    """Pull aggregate stats for a domain and return as a text summary."""
    client = get_client()
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    queries = {
        "transport": f"""
            SELECT
                COUNT(*) as total_events,
                AVG(CAST(JSON_VALUE(payload, '$.delay_minutes') AS FLOAT64)) as avg_delay,
                COUNT(DISTINCT JSON_VALUE(payload, '$.route_id')) as active_routes,
                COUNTIF(CAST(JSON_VALUE(payload, '$.delay_minutes') AS FLOAT64) > 10) as delayed_trips
            FROM {table('events')}
            WHERE domain = 'transport'
              AND timestamp >= '{cutoff}'
        """,
        "health": f"""
            SELECT
                COUNT(*) as total_records,
                AVG(CAST(JSON_VALUE(payload, '$.utilization_rate') AS FLOAT64)) as avg_utilization,
                COUNT(DISTINCT JSON_VALUE(payload, '$.facility_id')) as facilities,
                COUNTIF(JSON_VALUE(payload, '$.alert') = 'true') as alerts
            FROM {table('events')}
            WHERE domain = 'health'
              AND timestamp >= '{cutoff}'
        """,
        "education": f"""
            SELECT
                COUNT(*) as total_records,
                AVG(CAST(JSON_VALUE(payload, '$.enrollment_change_pct') AS FLOAT64)) as avg_enrollment_change,
                COUNT(DISTINCT JSON_VALUE(payload, '$.institution_id')) as institutions,
                SUM(CAST(JSON_VALUE(payload, '$.new_enrollments') AS INT64)) as total_new_enrollments
            FROM {table('events')}
            WHERE domain = 'education'
              AND timestamp >= '{cutoff}'
        """,
        "community": f"""
            SELECT
                COUNT(*) as total_feedback,
                AVG(CAST(JSON_VALUE(payload, '$.sentiment_score') AS FLOAT64)) as avg_sentiment,
                COUNT(DISTINCT JSON_VALUE(payload, '$.category')) as categories,
                COUNTIF(CAST(JSON_VALUE(payload, '$.sentiment_score') AS FLOAT64) < 0.3) as negative_items
            FROM {table('events')}
            WHERE domain = 'community'
              AND timestamp >= '{cutoff}'
        """,
    }
    
    sql = queries.get(domain, f"""
        SELECT COUNT(*) as total_events
        FROM {table('events')}
        WHERE timestamp >= '{cutoff}'
    """)
    
    try:
        rows = list(client.query(sql).result())
        if not rows:
            return f"No {domain} data found for the last {days} days."
        row = dict(rows[0])
        lines = [f"{k}: {v}" for k, v in row.items()]
        return f"{domain.title()} data summary (last {days} days):\n" + "\n".join(lines)
    except Exception as e:
        return f"Data summary unavailable: {str(e)}"


async def get_time_series(domain: str, metric: str, days: int = 30) -> list[dict]:
    """Return daily time series for a metric."""
    client = get_client()
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    sql = f"""
        SELECT
            DATE(timestamp) as date,
            AVG(CAST(JSON_VALUE(payload, '$.{metric}') AS FLOAT64)) as value,
            COUNT(*) as count
        FROM {table('events')}
        WHERE domain = '{domain}'
          AND timestamp >= '{cutoff}'
          AND JSON_VALUE(payload, '$.{metric}') IS NOT NULL
        GROUP BY date
        ORDER BY date ASC
    """
    
    try:
        rows = list(client.query(sql).result())
        return [{"date": str(r["date"]), "value": r["value"], "count": r["count"]} for r in rows]
    except Exception:
        return []


async def get_kpi_snapshot() -> dict:
    """Dashboard KPI snapshot across all domains."""
    client = get_client()
    
    sql = f"""
        SELECT
            domain,
            COUNT(*) as event_count,
            COUNTIF(JSON_VALUE(payload, '$.alert') = 'true') as alert_count
        FROM {table('events')}
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        GROUP BY domain
    """
    
    try:
        rows = list(client.query(sql).result())
        return {r["domain"]: {"events": r["event_count"], "alerts": r["alert_count"]} for r in rows}
    except Exception:
        return {}


async def create_events_table_if_not_exists():
    """Create the main events table in BigQuery (run once on setup)."""
    client = get_client()
    
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET}")
    dataset_ref.location = "US"
    try:
        client.create_dataset(dataset_ref, exists_ok=True)
    except Exception:
        pass
    
    schema = [
        bigquery.SchemaField("id",        "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("domain",    "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("source",    "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("payload",   "JSON",      mode="NULLABLE"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    table_ref = bigquery.Table(f"{PROJECT_ID}.{DATASET}.events", schema=schema)
    table_ref.time_partitioning = bigquery.TimePartitioning(field="timestamp")
    table_ref.clustering_fields = ["domain"]
    
    client.create_table(table_ref, exists_ok=True)