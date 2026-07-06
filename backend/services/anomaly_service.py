"""
services/anomaly_service.py
Scans recent BigQuery data for anomalies and fires alerts to Firestore.
Called on a schedule (Cloud Scheduler → /anomaly/scan endpoint).
"""
import os
from google.cloud import bigquery
from services.firestore_service import save_alert, get_alerts

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET    = os.environ.get("BQ_DATASET", "civicmind_data")


ANOMALY_RULES = {
    "transport": [
        {
            "name": "High transit delay",
            "sql": """
                SELECT AVG(CAST(JSON_VALUE(payload, '$.delay_minutes') AS FLOAT64)) as val
                FROM `{table}`
                WHERE domain = 'transport'
                  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
            """,
            "threshold": 15.0,
            "operator": "gt",
            "severity": "high",
            "title": "Transit delays exceeding 15 minutes",
            "description": "Average transit delay in the last hour is above the 15-minute threshold.",
        },
        {
            "name": "Incident spike",
            "sql": """
                SELECT COUNTIF(JSON_VALUE(payload, '$.incident') = 'true') as val
                FROM `{table}`
                WHERE domain = 'transport'
                  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR)
            """,
            "threshold": 10,
            "operator": "gt",
            "severity": "critical",
            "title": "High incident count on transit network",
            "description": "More than 10 transit incidents reported in the last 3 hours.",
        },
    ],
    "health": [
        {
            "name": "Clinic overcapacity",
            "sql": """
                SELECT MAX(CAST(JSON_VALUE(payload, '$.utilization_rate') AS FLOAT64)) as val
                FROM `{table}`
                WHERE domain = 'health'
                  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
            """,
            "threshold": 0.93,
            "operator": "gt",
            "severity": "critical",
            "title": "Clinic utilization above 93%",
            "description": "At least one clinic is operating near or above capacity. Patient overflow risk.",
        },
    ],
    "education": [
        {
            "name": "Enrollment drop",
            "sql": """
                SELECT MIN(CAST(JSON_VALUE(payload, '$.enrollment_change_pct') AS FLOAT64)) as val
                FROM `{table}`
                WHERE domain = 'education'
                  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
            """,
            "threshold": -5.0,
            "operator": "lt",
            "severity": "warning",
            "title": "Significant enrollment decline detected",
            "description": "At least one institution shows >5% enrollment drop in the last 24 hours.",
        },
    ],
    "community": [
        {
            "name": "Negative sentiment spike",
            "sql": """
                SELECT AVG(CAST(JSON_VALUE(payload, '$.sentiment_score') AS FLOAT64)) as val
                FROM `{table}`
                WHERE domain = 'community'
                  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 6 HOUR)
            """,
            "threshold": 0.3,
            "operator": "lt",
            "severity": "warning",
            "title": "Low community sentiment detected",
            "description": "Average citizen feedback sentiment dropped below 0.3 in the last 6 hours.",
        },
    ],
}


async def scan_for_anomalies() -> list[dict]:
    client   = bigquery.Client(project=PROJECT_ID)
    table_id = f"`{PROJECT_ID}.{DATASET}.events`"
    fired    = []

    for domain, rules in ANOMALY_RULES.items():
        for rule in rules:
            try:
                sql  = rule["sql"].format(table=table_id)
                rows = list(client.query(sql).result())
                if not rows:
                    continue

                val = rows[0]["val"]
                if val is None:
                    continue

                triggered = (
                    (rule["operator"] == "gt" and val > rule["threshold"]) or
                    (rule["operator"] == "lt" and val < rule["threshold"])
                )

                if triggered:
                    # Avoid duplicate alerts for same rule in last hour
                    existing = await get_alerts(domain=domain, limit=20)
                    already_open = any(
                        a.get("title") == rule["title"] and not a.get("resolved")
                        for a in existing
                    )
                    if not already_open:
                        alert_id = await save_alert({
                            "domain":      domain,
                            "title":       rule["title"],
                            "description": f"{rule['description']} (detected value: {round(float(val), 3)})",
                            "severity":    rule["severity"],
                        })
                        fired.append({"rule": rule["name"], "alert_id": alert_id, "value": val})

            except Exception as e:
                print(f"Anomaly scan error [{domain}/{rule['name']}]: {e}")

    return fired