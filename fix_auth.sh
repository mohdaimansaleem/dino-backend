#!/bin/bash

# Quick fix for authentication issue
echo "🔧 Fixing Cloud Run authentication..."

# Allow unauthenticated access
gcloud run services add-iam-policy-binding dino-backend-api \
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker"

echo "✅ Authentication fixed!"
echo "🧪 Testing health endpoint..."

# Test the health endpoint
curl -s https://dino-backend-api-1018711634531.us-central1.run.app/health | head -5

echo ""
echo "🎉 Service should now be accessible!"