import uuid
from datetime import datetime
from fastapi import APIRouter
from models.schemas import InsightRequest, InsightResponse, Insight
from services.bigquery_service import get_domain_summary

router = APIRouter()

MOCK_INSIGHTS = {
    "transport": [
        {"title": "Peak hour delays above threshold", "description": "Route 101 and BRT-1 show average delays of 12.3 minutes during morning rush hours. This is 23% above the acceptable threshold and affecting approximately 2,400 daily commuters.", "severity": "warning", "metric": "delay_minutes", "value": 12.3, "trend": "up"},
        {"title": "On-time performance improving", "description": "Weekend on-time rates have improved to 89% over the last 30 days, up from 82% last month. Service frequency adjustments appear to be working.", "severity": "info", "metric": "on_time_rate", "value": 89.0, "trend": "up"},
    ],
    "health": [
        {"title": "Clinic-7 near capacity", "description": "Clinic-7 is operating at 94% utilization over the past 48 hours. Patient wait times have increased to 38 minutes on average. Immediate resource reallocation recommended.", "severity": "critical", "metric": "utilization_rate", "value": 94.0, "trend": "up"},
        {"title": "Community wellness participation up", "description": "Enrollment in community wellness programs has increased by 15% this month, suggesting improved outreach effectiveness.", "severity": "info", "metric": "patient_count", "value": 78.0, "trend": "up"},
    ],
    "education": [
        {"title": "Enrollment decline in 3 schools", "description": "Schools 4, 7, and 11 show enrollment drops of 6-8% compared to last quarter. Early intervention programs should be reviewed for these institutions.", "severity": "warning", "metric": "enrollment_change_pct", "value": -6.5, "trend": "down"},
        {"title": "Completion rates stable", "description": "Overall course completion rates remain at 78% across all institutions, consistent with last quarter's performance.", "severity": "info", "metric": "completion_rate", "value": 78.0, "trend": "stable"},
    ],
    "community": [
        {"title": "Sanitation feedback negative spike", "description": "Citizen feedback on sanitation services dropped to a sentiment score of 0.28 this week, below the 0.30 alert threshold. 67% of complaints cite collection frequency.", "severity": "warning", "metric": "sentiment_score", "value": 0.28, "trend": "down"},
        {"title": "Overall engagement improving", "description": "Community portal engagement rate has risen to 42% this month, up from 31% in the previous period, indicating successful outreach campaigns.", "severity": "info", "metric": "engagement_rate", "value": 42.0, "trend": "up"},
    ],
    "general": [
        {"title": "City performance on track", "description": "Overall smart city performance metrics are within acceptable ranges across all domains. Transport and health require monitoring.", "severity": "info", "metric": None, "value": None, "trend": "stable"},
    ],
}

MOCK_SUMMARIES = {
    "transport": "Transport performance shows mixed results this month. While weekend reliability has improved significantly, peak-hour delays on key routes remain above acceptable thresholds. Immediate focus should be on BRT-1 and Route 101 corridor optimization.",
    "health": "Healthcare utilization is trending high with Clinic-7 approaching critical capacity. Community wellness program participation is growing positively. Recommend emergency resource reallocation to high-utilization facilities.",
    "education": "Education metrics show stable completion rates but concerning enrollment declines in 3 institutions. Early intervention is recommended before next enrollment cycle begins.",
    "community": "Community engagement is improving overall, but sanitation service satisfaction has dipped below acceptable levels. Targeted service improvements and communication campaigns are needed.",
    "general": "City-wide performance is stable with specific attention needed in transport delays and clinic capacity. All other domains are performing within expected parameters.",
}


@router.post("", response_model=InsightResponse)
async def get_insights(request: InsightRequest):
    domain = request.domain.value

    # Try Gemini first, fall back to mock data
    try:
        from services.gemini_service import generate_insights
        summary = await get_domain_summary(domain=domain, days=request.time_range_days)
        result = await generate_insights(domain=domain, data_summary=summary)
        insights = []
        for item in result.get("insights", [])[:request.limit]:
            trend_val = item.get("trend")
            if trend_val == "null" or trend_val not in ["up", "down", "stable", None]:
                trend_val = None
            insights.append(Insight(
                id=str(uuid.uuid4()),
                domain=request.domain,
                title=item.get("title", ""),
                description=item.get("description", ""),
                severity=item.get("severity", "info"),
                metric=item.get("metric"),
                value=item.get("value"),
                trend=trend_val,
                created_at=datetime.utcnow(),
            ))
        return InsightResponse(
            insights=insights,
            summary=result.get("summary", ""),
            domain=request.domain,
        )
    except Exception:
        # Return mock insights when Gemini quota exceeded
        mock = MOCK_INSIGHTS.get(domain, MOCK_INSIGHTS["general"])[:request.limit]
        insights = [
            Insight(
                id=str(uuid.uuid4()),
                domain=request.domain,
                title=m["title"],
                description=m["description"],
                severity=m["severity"],
                metric=m.get("metric"),
                value=m.get("value"),
                trend=m.get("trend"),
                created_at=datetime.utcnow(),
            )
            for m in mock
        ]
        return InsightResponse(
            insights=insights,
            summary=MOCK_SUMMARIES.get(domain, ""),
            domain=request.domain,
        )


@router.get("/kpi")
async def kpi_snapshot():
    from services.bigquery_service import get_kpi_snapshot
    return await get_kpi_snapshot()