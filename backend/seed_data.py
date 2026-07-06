"""
seed_data.py — Uses CSV load job instead of streaming insert (works on free tier)
Usage: python seed_data.py --project YOUR_PROJECT_ID
"""
import os
import json
import uuid
import random
import argparse
import tempfile
import csv
from datetime import datetime, timedelta
from google.cloud import bigquery

random.seed(42)


def generate_transport(days):
    routes = ["101", "102", "103", "202", "305", "BRT-1", "METRO-A", "METRO-B"]
    records = []
    base = datetime.utcnow() - timedelta(days=days)
    for i in range(days * 24):
        ts = base + timedelta(hours=i)
        hour = ts.hour
        rush = hour in (8, 9, 17, 18, 19)
        delay = random.gauss(8 if rush else 3, 4 if rush else 2)
        delay = max(0, delay)
        records.append({
            "id": str(uuid.uuid4()),
            "domain": "transport",
            "source": "gtfs-realtime",
            "payload": json.dumps({
                "route_id": random.choice(routes),
                "delay_minutes": round(delay, 1),
                "passenger_count": random.randint(20 if rush else 5, 280 if rush else 120),
                "on_time_rate": round(random.uniform(0.6, 0.98), 2),
                "incident": "true" if delay > 15 else "false",
                "alert": "true" if delay > 20 else "false",
            }),
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
        })
    return records


def generate_health(days):
    facilities = [f"clinic-{i}" for i in range(1, 9)]
    records = []
    base = datetime.utcnow() - timedelta(days=days)
    for i in range(days * 12):
        ts = base + timedelta(hours=i * 2)
        for fac in facilities:
            util = random.gauss(0.72, 0.12)
            util = min(max(util, 0.2), 1.0)
            records.append({
                "id": str(uuid.uuid4()),
                "domain": "health",
                "source": "clinic-ehr",
                "payload": json.dumps({
                    "facility_id": fac,
                    "utilization_rate": round(util, 2),
                    "patient_count": random.randint(10, 90),
                    "wait_time_minutes": round(random.gauss(22, 10), 1),
                    "beds_available": random.randint(0, 20),
                    "alert": "true" if util > 0.92 else "false",
                }),
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
            })
    return records


def generate_education(days):
    institutions = [f"school-{i}" for i in range(1, 13)]
    records = []
    base = datetime.utcnow() - timedelta(days=days)
    for i in range(days):
        ts = base + timedelta(days=i)
        for inst in institutions:
            enroll_change = random.gauss(0.5, 3.0)
            records.append({
                "id": str(uuid.uuid4()),
                "domain": "education",
                "source": "enrollment-db",
                "payload": json.dumps({
                    "institution_id": inst,
                    "enrollment_change_pct": round(enroll_change, 2),
                    "new_enrollments": random.randint(0, 15),
                    "completion_rate": round(random.uniform(0.65, 0.95), 2),
                    "dropout_risk_count": random.randint(0, 8),
                    "alert": "true" if enroll_change < -5 else "false",
                }),
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
            })
    return records


def generate_community(days):
    categories = ["transport", "health", "sanitation", "parks", "safety", "housing", "education"]
    records = []
    base = datetime.utcnow() - timedelta(days=days)
    for i in range(days * 8):
        ts = base + timedelta(hours=i * 3)
        count = random.randint(3, 25)
        sentiment = random.gauss(0.58, 0.2)
        sentiment = min(max(sentiment, 0.0), 1.0)
        records.append({
            "id": str(uuid.uuid4()),
            "domain": "community",
            "source": "feedback-portal",
            "payload": json.dumps({
                "category": random.choice(categories),
                "sentiment_score": round(sentiment, 2),
                "response_count": count,
                "engagement_rate": round(random.uniform(0.1, 0.6), 2),
                "negative_count": int(count * (1 - sentiment)),
                "alert": "true" if sentiment < 0.25 else "false",
            }),
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
        })
    return records


def load_via_csv(client, table_id, records):
    """Write records to a temp CSV and load into BigQuery using a load job."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "domain", "source", "payload", "timestamp"])
        writer.writeheader()
        writer.writerows(records)
        tmp_path = f.name

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=[
            bigquery.SchemaField("id",        "STRING",    mode="REQUIRED"),
            bigquery.SchemaField("domain",     "STRING",    mode="REQUIRED"),
            bigquery.SchemaField("source",     "STRING",    mode="NULLABLE"),
            bigquery.SchemaField("payload",    "STRING",    mode="NULLABLE"),
            bigquery.SchemaField("timestamp",  "TIMESTAMP", mode="REQUIRED"),
        ],
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    with open(tmp_path, "rb") as f:
        job = client.load_table_from_file(f, table_id, job_config=job_config)
    job.result()

    os.unlink(tmp_path)
    return job.output_rows


def seed(project_id, dataset, days):
    client   = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{dataset}.events"

    dataset_ref = bigquery.Dataset(f"{project_id}.{dataset}")
    dataset_ref.location = "US"
    client.create_dataset(dataset_ref, exists_ok=True)

    schema = [
        bigquery.SchemaField("id",        "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("domain",    "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("source",    "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("payload",   "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    ]
    table_obj = bigquery.Table(table_id, schema=schema)
    table_obj.time_partitioning = bigquery.TimePartitioning(field="timestamp")
    table_obj.clustering_fields = ["domain"]
    client.create_table(table_obj, exists_ok=True)
    print(f"✅ Table ready: {table_id}")

    generators = {
        "transport": generate_transport,
        "health":    generate_health,
        "education": generate_education,
        "community": generate_community,
    }

    for domain, gen_fn in generators.items():
        print(f"   Generating {domain} data ...", end=" ", flush=True)
        records = gen_fn(days)
        rows = load_via_csv(client, table_id, records)
        print(f"{rows} rows loaded ✅")

    print("\n🎉 Seeding complete! BigQuery is ready.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=os.environ.get("GCP_PROJECT_ID", ""))
    parser.add_argument("--dataset", default="civicmind_data")
    parser.add_argument("--days",    type=int, default=30)
    args = parser.parse_args()

    if not args.project:
        raise SystemExit("Pass --project YOUR_PROJECT_ID or set GCP_PROJECT_ID")

    seed(args.project, args.dataset, args.days)