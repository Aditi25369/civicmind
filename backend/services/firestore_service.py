import os
import uuid
from datetime import datetime
from google.cloud import firestore

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
_db = None


def init_firestore():
    global _db
    _db = firestore.AsyncClient(project=PROJECT_ID)


def get_db():
    if _db is None:
        init_firestore()
    return _db


async def create_session(domain: str) -> str:
    session_id = str(uuid.uuid4())
    await get_db().collection("sessions").document(session_id).set({
        "domain": domain,
        "created_at": datetime.utcnow(),
        "messages": [],
    })
    return session_id


async def get_session(session_id: str):
    doc = await get_db().collection("sessions").document(session_id).get()
    return doc.to_dict() if doc.exists else None


async def append_message(session_id: str, role: str, content: str):
    ref = get_db().collection("sessions").document(session_id)
    await ref.update({
        "messages": firestore.ArrayUnion([{
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }])
    })


async def save_alert(alert: dict) -> str:
    alert_id = str(uuid.uuid4())
    await get_db().collection("alerts").document(alert_id).set({
        **alert,
        "id": alert_id,
        "created_at": datetime.utcnow(),
        "resolved": False,
    })
    return alert_id


async def get_alerts(domain: str = None, limit: int = 20) -> list:
    ref = get_db().collection("alerts").order_by(
        "created_at", direction=firestore.Query.DESCENDING
    ).limit(limit)
    if domain:
        ref = ref.where("domain", "==", domain)
    docs = await ref.get()
    alerts = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if hasattr(data.get("created_at"), "isoformat"):
            data["created_at"] = data["created_at"].isoformat()
        alerts.append(data)
    return alerts


async def resolve_alert(alert_id: str):
    await get_db().collection("alerts").document(alert_id).update({
        "resolved": True,
        "resolved_at": datetime.utcnow(),
    })