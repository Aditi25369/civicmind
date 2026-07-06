import os
import json
import uuid
from datetime import datetime
from google.cloud import pubsub_v1

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
TOPIC_ID   = os.environ.get("PUBSUB_TOPIC", "civicmind-events")
_publisher = None


def init_pubsub():
    global _publisher
    _publisher = pubsub_v1.PublisherClient()
    _ensure_topic()


def get_publisher():
    if _publisher is None:
        init_pubsub()
    return _publisher


def _ensure_topic():
    pub = get_publisher()
    topic_path = pub.topic_path(PROJECT_ID, TOPIC_ID)
    try:
        pub.create_topic(request={"name": topic_path})
    except Exception:
        pass


async def publish_event(domain: str, source: str, payload: dict) -> str:
    pub = get_publisher()
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