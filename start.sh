#!/bin/bash

# Startup script for Dino E-Menu Backend
set -e

echo "🚀 Starting Dino E-Menu Backend..."

# Set default port if not provided
export PORT=${PORT:-8080}

echo "📡 Port: $PORT"
echo "🌍 Environment: ${ENVIRONMENT:-production}"
echo "📦 Project: ${GCP_PROJECT_ID:-unknown}"

# Validate required environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY environment variable is required"
    exit 1
fi

if [ -z "$GCP_PROJECT_ID" ]; then
    echo "❌ ERROR: GCP_PROJECT_ID environment variable is required"
    exit 1
fi

echo "✅ Environment variables validated"

# Start the application with error handling
echo "🎯 Starting uvicorn server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --log-level info \
    --access-log