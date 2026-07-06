from fastapi import APIRouter
from models.schemas import AlertsResponse
from services.firestore_service import get_alerts, resolve_alert

router = APIRouter()


@router.get("", response_model=AlertsResponse)
async def list_alerts(domain: str = None, limit: int = 20):
    alerts = await get_alerts(domain=domain, limit=limit)
    unresolved = sum(1 for a in alerts if not a.get("resolved"))
    return AlertsResponse(alerts=alerts, total=len(alerts), unresolved=unresolved)


@router.patch("/{alert_id}/resolve")
async def resolve(alert_id: str):
    await resolve_alert(alert_id)
    return {"status": "resolved", "alert_id": alert_id}