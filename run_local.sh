#!/bin/bash
# run_local.sh — Start backend + frontend together for local dev
# Usage: chmod +x run_local.sh && ./run_local.sh

set -e

# Check GCP_PROJECT_ID
if [ -z "$GCP_PROJECT_ID" ]; then
  if [ -f backend/.env ]; then
    export $(grep -v '^#' backend/.env | xargs)
  else
    echo "❌  Create backend/.env from backend/.env.example first"
    exit 1
  fi
fi

echo "🚀 Starting CivicMind locally…"
echo "   Project: $GCP_PROJECT_ID"

# Backend in background
echo ""
echo "==> Starting FastAPI backend on :8080"
cd backend
pip install -r requirements.txt -q
uvicorn main:app --reload --port 8080 &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 3
echo "   Backend PID: $BACKEND_PID"

# Frontend
echo ""
echo "==> Starting React frontend on :3000"
cd frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ CivicMind running!"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8080"
echo "   API docs:  http://localhost:8080/docs"
echo ""
echo "Press Ctrl+C to stop both services"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait