"""
subscriber.py — Cloud Run Job
Pulls from Pub/Sub civicmind-events topic and writes to BigQuery.
Run as a separate Cloud Run service or deploy as a Cloud Run Job.
"""
import os
import json
import uuid
import logging
from datetime import datetime
from concurrent.futures import TimeoutError

from google.cloud import pubsub_v1, bigquery

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("subscriber")

PROJECT_ID   = os.environ["GCP_PROJECT_ID"]
TOPIC_ID     = os.environ.get("PUBSUB_TOPIC", "civicmind-events")
SUB_ID       = os.environ.get("PUBSUB_SUB", "civicmind-bq-sub")
DATASET      = os.environ.get("BQ_DATASET", "civicmind_data")
TABLE        = "events"

bq_client  = bigquery.Client(project=PROJECT_ID)
table_ref  = f"{PROJECT_ID}.{DATASET}.{TABLE}"


def write_to_bq(records: list[dict]):
    rows = []
    for r in records:
        rows.append({
            "id":        r.get("id", str(uuid.uuid4())),
            "domain":    r.get("domain", "general"),
            "source":    r.get("source", "pubsub"),
            "payload":   json.dumps(r.get("payload", {})),
            "timestamp": r.get("timestamp", datetime.utcnow().isoformat()),
        })
    errors = bq_client.insert_rows_json(table_ref, rows)
    if errors:
        log.error("BQ insert errors: %s", errors)
    else:
        log.info("Wrote %d rows to BigQuery", len(rows))


def callback(message: pubsub_v1.subscriber.message.Message):
    try:
        data = json.loads(message.data.decode("utf-8"))
        write_to_bq([data])
        message.ack()
    except Exception as e:
        log.error("Failed to process message: %s", e)
        message.nack()


def main():
    subscriber = pubsub_v1.SubscriberClient()
    sub_path   = subscriber.subscription_path(PROJECT_ID, SUB_ID)

    # Create subscription if missing
    try:
        topic_path = f"projects/{PROJECT_ID}/topics/{TOPIC_ID}"
        subscriber.create_subscription(
            request={"name": sub_path, "topic": topic_path}
        )
        log.info("Created subscription %s", sub_path)
    except Exception:
        pass  # already exists

    log.info("Listening on %s …", sub_path)
    streaming_pull = subscriber.subscribe(sub_path, callback=callback)

    try:
        streaming_pull.result(timeout=None)   # runs forever
    except (KeyboardInterrupt, TimeoutError):
        streaming_pull.cancel()
        streaming_pull.result()


if __name__ == "__main__":
    main()