#!/bin/bash
# setup_gcp.sh — Run once to provision all CivicMind GCP resources
# Usage: chmod +x setup_gcp.sh && ./setup_gcp.sh your-project-id

set -e

PROJECT_ID=${1:-"civicmind-demo"}
REGION="us-central1"
DATASET="civicmind_data"
TOPIC="civicmind-events"
BUCKET="${PROJECT_ID}-civicmind-docs"

echo "==> Setting up CivicMind on GCP project: $PROJECT_ID"

gcloud config set project $PROJECT_ID

echo "==> Enabling APIs…"
gcloud services enable \
  run.googleapis.com \
  bigquery.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  firebase.googleapis.com

echo "==> Creating BigQuery dataset…"
bq --location=US mk --dataset "${PROJECT_ID}:${DATASET}" 2>/dev/null || true

echo "==> Creating Pub/Sub topic…"
gcloud pubsub topics create $TOPIC 2>/dev/null || true

echo "==> Creating BigQuery subscription for Pub/Sub…"
gcloud pubsub subscriptions create civicmind-bq-sub \
  --topic=$TOPIC \
  --bigquery-table="${PROJECT_ID}:${DATASET}.raw_events" \
  --create-schema \
  --write-metadata 2>/dev/null || true

echo "==> Creating Cloud Storage bucket for RAG documents…"
gsutil mb -l $REGION "gs://${BUCKET}" 2>/dev/null || true

echo "==> Creating Firestore database…"
gcloud firestore databases create --location=$REGION 2>/dev/null || true

echo "==> Creating Vertex AI Search datastore…"
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/global/collections/default_collection/dataStores?dataStoreId=civicmind-docs" \
  -d '{
    "displayName": "CivicMind Documents",
    "industryVertical": "GENERIC",
    "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
    "contentConfig": "CONTENT_REQUIRED",
    "searchTier": "STANDARD"
  }' 2>/dev/null || true

echo "==> Creating service account for Cloud Run…"
gcloud iam service-accounts create civicmind-api-sa \
  --display-name="CivicMind API Service Account" 2>/dev/null || true

SA="civicmind-api-sa@${PROJECT_ID}.iam.gserviceaccount.com"

for ROLE in \
  roles/bigquery.dataEditor \
  roles/bigquery.jobUser \
  roles/datastore.user \
  roles/pubsub.publisher \
  roles/aiplatform.user \
  roles/discoveryengine.viewer \
  roles/storage.objectViewer; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA" \
    --role="$ROLE" --quiet
done

echo ""
echo "✅ GCP setup complete!"
echo ""
echo "Next steps:"
echo "  1. Upload documents to gs://${BUCKET} for RAG"
echo "  2. Connect Cloud Storage bucket to Vertex AI Search datastore"
echo "  3. Deploy backend:  gcloud builds submit"
echo "  4. Set VITE_API_URL and deploy frontend: firebase deploy"
echo ""
echo "Environment variables for Cloud Run:"
echo "  GCP_PROJECT_ID=$PROJECT_ID"
echo "  GCP_LOCATION=$REGION"
echo "  BQ_DATASET=$DATASET"
echo "  PUBSUB_TOPIC=$TOPIC"
echo "  VERTEX_DATASTORE_ID=civicmind-docs"