import os
import uuid
from datetime import datetime

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
_db = None


def init_firestore():
    global _db
    try:
        from google.cloud import firestore
        _db = firestore.AsyncClient(project=PROJECT_ID)
    except Exception as e:
        print(f"Firestore init failed (non-fatal): {e}")
        _db = None


def get_db():
    if _db is None:
        init_firestore()
    return _db


async def create_session(domain: str) -> str:
    session_id = str(uuid.uuid4())
    try:
        from google.cloud import firestore as fs
        await get_db().collection("sessions").document(session_id).set({
            "domain": domain,
            "created_at": datetime.utcnow(),
            "messages": [],
        })
    except Exception:
        pass
    return session_id


async def get_session(session_id: str):
    try:
        doc = await get_db().collection("sessions").document(session_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception:
        return None


async def append_message(session_id: str, role: str, content: str):
    try:
        from google.cloud import firestore as fs
        ref = get_db().collection("sessions").document(session_id)
        await ref.update({
            "messages": fs.ArrayUnion([{
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }])
        })
    except Exception:
        pass


async def save_alert(alert: dict) -> str:
    alert_id = str(uuid.uuid4())
    try:
        await get_db().collection("alerts").document(alert_id).set({
            **alert,
            "id": alert_id,
            "created_at": datetime.utcnow(),
            "resolved": False,
        })
    except Exception:
        pass
    return alert_id


async def get_alerts(domain: str = None, limit: int = 20) -> list:
    try:
        from google.cloud import firestore as fs
        ref = get_db().collection("alerts").order_by(
            "created_at", direction=fs.Query.DESCENDING
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
    except Exception:
        return []


async def resolve_alert(alert_id: str):
    try:
        await get_db().collection("alerts").document(alert_id).update({
            "resolved": True,
            "resolved_at": datetime.utcnow(),
        })
    except Exception:
        pass