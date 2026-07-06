"""/anomaly — scan endpoint called by Cloud Scheduler every 15 minutes."""
from fastapi import APIRouter
from services.anomaly_service import scan_for_anomalies

router = APIRouter()


@router.post("/scan")
async def scan():
    fired = await scan_for_anomalies()
    return {
        "status": "ok",
        "alerts_fired": len(fired),
        "details": fired,
    }