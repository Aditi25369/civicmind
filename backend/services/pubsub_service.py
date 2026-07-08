import os
import json
import uuid
from datetime import datetime

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
TOPIC_ID   = os.environ.get("PUBSUB_TOPIC", "civicmind-events")
_publisher = None


def init_pubsub():
    global _publisher
    try:
        from google.cloud import pubsub_v1
        _publisher = pubsub_v1.PublisherClient()
    except Exception as e:
        print(f"Pub/Sub init failed (non-fatal): {e}")
        _publisher = None


def get_publisher():
    if _publisher is None:
        init_pubsub()
    return _publisher


async def publish_event(domain: str, source: str, payload: dict) -> str:
    try:
        pub = get_publisher()
        if pub is None:
            return str(uuid.uuid4())
        topic_path = pub.topic_path(PROJECT_ID, TOPIC_ID)
        message = {
            "id": str(uuid.uuid4()),
            "domain": domain,
            "source": source,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
        data = json.dumps(message).encode("utf-8")
        future = pub.publish(topic_path, data, domain=domain, source=source)
        return future.result()
    except Exception:
        return str(uuid.uuid4())


async def publish_batch(records: list) -> list:
    message_ids = []
    for record in records:
        mid = await publish_event(
            domain=record["domain"],
            source=record.get("source", "api"),
            payload=record.get("payload", {}),
        )
        message_ids.append(mid)
    return message_ids