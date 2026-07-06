from fastapi import APIRouter
from models.schemas import IngestRequest, IngestResponse
from services.pubsub_service import publish_batch

router = APIRouter()


@router.post("", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    records = [r.model_dump() for r in request.records]
    message_ids = await publish_batch(records)
    return IngestResponse(
        accepted=len(message_ids),
        rejected=len(records) - len(message_ids),
        message_ids=message_ids,
    )