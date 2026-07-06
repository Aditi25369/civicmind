# CivicMind — AI Decision Intelligence Platform

AI-powered platform for smarter city governance using exclusively Google Cloud.

## Stack (100% Google)

| Layer | Service |
|-------|---------|
| AI / NL queries | Gemini 1.5 Pro via Vertex AI |
| RAG / document search | Vertex AI Search |
| Forecasting | Vertex AI AutoML + Gemini |
| Analytics warehouse | BigQuery |
| Real-time ingestion | Cloud Pub/Sub |
| Session / alert storage | Firestore |
| Document storage | Cloud Storage |
| Backend runtime | Cloud Run (FastAPI) |
| Frontend hosting | Firebase Hosting |
| CI/CD | Cloud Build |
| Secrets | Secret Manager |

## Domains

- Transport & Mobility — GTFS, traffic, route optimization
- Healthcare & Well-being — clinic utilization, wellness monitoring
- Education & Economic Development — enrollment, workforce
- Community Intelligence — citizen feedback, sentiment analysis

## Quick start

### 1. Provision GCP
```bash
chmod +x setup_gcp.sh
./setup_gcp.sh YOUR_PROJECT_ID
```

### 2. Run backend locally
```bash
cd backend
cp .env.example .env   # fill in your project ID
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

### 3. Run frontend locally
```bash
cd frontend
npm install
npm run dev
```

### 4. Deploy to GCP
```bash
# Backend → Cloud Run via Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Frontend → Firebase Hosting
cd frontend && npm run build
firebase deploy --only hosting
```

## Project structure

civicmind/
├── run_local.sh                        ← root
├── setup_gcp.sh                        ← root
├── cloudbuild.yaml                     ← root
├── firebase.json                       ← root
│
├── backend/
│   ├── main.py
│   ├── subscriber.py                   ← ADD HERE
│   ├── seed_data.py                    ← ADD HERE
│   ├── .env                            ← ADD HERE (copy from .env.example)
│   ├── .env.example                    ← ADD HERE
│   ├── Dockerfile
│   ├── Dockerfile.subscriber           ← ADD HERE
│   ├── requirements.txt
│   │
│   ├── agents/                         ← CREATE THIS FOLDER
│   │   ├── __init__.py                 ← ADD (empty file)
│   │   └── coordinator.py              ← ADD HERE
│   │
│   ├── models/
│   │   ├── __init__.py                 ← ADD (empty file)
│   │   └── schemas.py
│   │
│   ├── routers/
│   │   ├── __init__.py                 ← ADD (empty file)
│   │   ├── query.py
│   │   ├── insights.py
│   │   ├── forecast.py
│   │   ├── alerts.py
│   │   ├── ingest.py
│   │   └── anomaly.py                  ← ADD HERE
│   │
│   └── services/
│       ├── __init__.py                 ← ADD (empty file)
│       ├── gemini_service.py
│       ├── bigquery_service.py
│       ├── firestore_service.py
│       ├── pubsub_service.py
│       └── anomaly_service.py          ← ADD HERE
│
└── frontend/
    ├── index.html                      ← ADD HERE (root of frontend/)
    ├── package.json
    ├── vite.config.js
    ├── .env                            ← ADD HERE
    └── src/
        ├── main.jsx                    ← ADD HERE
        ├── App.jsx
        ├── App.css
        ├── components/
        │   └── Sidebar.jsx
        ├── pages/
        │   ├── Dashboard.jsx
        │   ├── ChatPage.jsx
        │   ├── DomainPage.jsx
        │   └── AlertsPage.jsx
        └── services/
            └── api.js

## Ingest sample data

```bash
curl -X POST http://localhost:8080/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "domain": "transport",
        "source": "gtfs-feed",
        "payload": {"route_id": "101", "delay_minutes": 12, "passenger_count": 240}
      },
      {
        "domain": "health",
        "source": "clinic-api",
        "payload": {"facility_id": "clinic-7", "utilization_rate": 0.87, "alert": "false"}
      }
    ]
  }'
```