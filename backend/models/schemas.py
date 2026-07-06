from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class DomainType(str, Enum):
    TRANSPORT = "transport"
    HEALTH = "health"
    EDUCATION = "education"
    COMMUNITY = "community"
    GENERAL = "general"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    domain: DomainType = DomainType.GENERAL
    session_id: Optional[str] = None
    history: List[ChatMessage] = []
    use_rag: bool = True


class QueryResponse(BaseModel):
    answer: str
    sources: List[str] = []
    domain: DomainType
    session_id: str
    suggested_actions: List[str] = []
    follow_up_questions: List[str] = []


class DataRecord(BaseModel):
    domain: DomainType
    source: str
    payload: dict
    timestamp: Optional[datetime] = None


class IngestRequest(BaseModel):
    records: List[DataRecord]


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    message_ids: List[str]


class InsightRequest(BaseModel):
    domain: DomainType
    time_range_days: int = Field(default=30, ge=1, le=365)
    limit: int = Field(default=5, ge=1, le=20)


class Insight(BaseModel):
    id: str
    domain: DomainType
    title: str
    description: str
    severity: Literal["info", "warning", "critical"]
    metric: Optional[str] = None
    value: Optional[float] = None
    trend: Optional[Literal["up", "down", "stable"]] = None
    created_at: datetime


class InsightResponse(BaseModel):
    insights: List[Insight]
    summary: str
    domain: DomainType


class Alert(BaseModel):
    id: str
    domain: DomainType
    title: str
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    created_at: datetime
    resolved: bool = False


class AlertsResponse(BaseModel):
    alerts: List[Alert]
    total: int
    unresolved: int


class ForecastRequest(BaseModel):
    domain: DomainType
    metric: str
    horizon_days: int = Field(default=7, ge=1, le=90)


class ForecastPoint(BaseModel):
    date: str
    value: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    domain: DomainType
    metric: str
    forecast: List[ForecastPoint]
    model_used: str
    confidence: float