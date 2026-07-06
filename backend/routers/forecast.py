import os
import random
from datetime import datetime, timedelta
from fastapi import APIRouter
from models.schemas import ForecastRequest, ForecastResponse, ForecastPoint

router = APIRouter()

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
LOCATION   = os.environ.get("GCP_LOCATION", "us-central1")


def _mock_forecast(domain: str, metric: str, horizon: int) -> list:
    base_values = {
        "delay_minutes":        8.5,
        "passenger_count":      145.0,
        "on_time_rate":         0.82,
        "utilization_rate":     0.74,
        "patient_count":        52.0,
        "wait_time_minutes":    24.0,
        "enrollment_change_pct": 0.8,
        "new_enrollments":      7.0,
        "completion_rate":      0.78,
        "sentiment_score":      0.61,
        "engagement_rate":      0.38,
        "response_count":       14.0,
    }
    base = base_values.get(metric, 50.0)
    points = []
    for i in range(horizon):
        date = (datetime.utcnow() + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        drift = random.uniform(-0.03, 0.04)
        v = max(0, base * (1 + drift * (i + 1)))
        points.append(ForecastPoint(
            date=date,
            value=round(v, 2),
            lower_bound=round(v * 0.90, 2),
            upper_bound=round(v * 1.10, 2),
        ))
        base = v
    return points


@router.post("", response_model=ForecastResponse)
async def forecast(request: ForecastRequest):
    try:
        from services.bigquery_service import get_time_series
        from services.gemini_service import client

        historical = await get_time_series(
            domain=request.domain.value,
            metric=request.metric,
            days=90,
        )

        if not historical:
            raise ValueError("No historical data")

        vals = [h["value"] for h in historical if h["value"] is not None]
        base = sum(vals) / len(vals) if vals else 50.0

        hist_summary = "\n".join(
            f"{h['date']}: {h['value']:.2f}" for h in historical[-14:]
        )

        prompt = f"""You are a time-series forecasting model for a Smart City.
Domain: {request.domain.value}
Metric: {request.metric}
Historical data (last 14 days):
{hist_summary}

Generate a {request.horizon_days}-day forecast starting from tomorrow.
Respond ONLY with a JSON array of {request.horizon_days} objects:
[
  {{"date": "YYYY-MM-DD", "value": <float>, "lower_bound": <float>, "upper_bound": <float>}}
]"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        import json
        raw = json.loads(text)
        points = [ForecastPoint(**item) for item in raw]

        return ForecastResponse(
            domain=request.domain,
            metric=request.metric,
            forecast=points,
            model_used="gemini-2.5-flash",
            confidence=0.82,
        )

    except Exception:
        # Fall back to mock forecast
        points = _mock_forecast(request.domain.value, request.metric, request.horizon_days)
        return ForecastResponse(
            domain=request.domain,
            metric=request.metric,
            forecast=points,
            model_used="mock-forecast",
            confidence=0.75,
        )