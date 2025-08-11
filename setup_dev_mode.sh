#!/bin/bash

# Setup Development Mode for Dino Backend
echo "🦕 Setting up Dino Backend Development Mode..."

# Set development mode environment variable
export DEV_MODE=true
export ENVIRONMENT=development
export DEBUG=true
export LOG_LEVEL=DEBUG

# Set a development secret key (change this in production!)
export SECRET_KEY="dev-secret-key-for-testing-only-change-in-production-32-chars"

# Set development GCP settings (these won't be used in dev mode)
export GCP_PROJECT_ID="dev-project"
export DATABASE_NAME="dev-database"
export GCS_BUCKET_NAME="dev-bucket"

echo "✅ Development mode environment variables set:"
echo "   DEV_MODE: $DEV_MODE"
echo "   ENVIRONMENT: $ENVIRONMENT"
echo "   DEBUG: $DEBUG"
echo "   LOG_LEVEL: $LOG_LEVEL"

echo ""
echo "🚀 You can now start the server with:"
echo "   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080"
echo ""
echo "🧪 Test the workspace endpoint:"
echo "   curl http://localhost:8080/api/v1/workspaces/public-debug"
echo "   curl http://localhost:8080/api/v1/workspaces?page=1&page_size=10"
echo ""
echo "📝 Note: This uses mock data. To use real Firestore data, set DEV_MODE=false"
echo "   and configure Google Cloud authentication."