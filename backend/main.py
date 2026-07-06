"""
CivicMind – AI Decision Intelligence Platform
Backend: FastAPI → deployed on Cloud Run
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import query, ingest, insights, alerts, forecast, anomaly
from services.firestore_service import init_firestore
from services.pubsub_service import init_pubsub


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_firestore()
    init_pubsub()
    yield


app = FastAPI(
    title="CivicMind API",
    description="AI-powered Decision Intelligence Platform for Smart Cities",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router,    prefix="/query",    tags=["query"])
app.include_router(ingest.router,   prefix="/ingest",   tags=["ingest"])
app.include_router(insights.router, prefix="/insights", tags=["insights"])
app.include_router(alerts.router,   prefix="/alerts",   tags=["alerts"])
app.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
app.include_router(anomaly.router,  prefix="/anomaly",  tags=["anomaly"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "civicmind-api"}


@app.get("/")
async def root():
    return {
        "message": "CivicMind Decision Intelligence Platform",
        "docs": "/docs",
        "modules": ["transport", "health", "education", "community"],
    }