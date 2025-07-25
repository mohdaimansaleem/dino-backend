#!/bin/bash
. .env.production.sh

gcloud alpha run deploy ${CLOUD_RUN_SERVICE_NAME} \
  --image ${CLOUD_RUN_IMAGE_NAME} \
  --platform managed \
  --no-allow-unauthenticated \
  --region ${GCP_REGION} \
  --project ${GCP_PROJECT_ID} \
  --memory 2G \
  --cpu 1 \
  --concurrency 20 \
  --max-instances 40 \
  --timeout 900 \
  --ingress all \
  --set-env-vars "ENVIRONMENT=${ENVIRONMENT}" \
  --set-env-vars "GCP_PROJECT_ID=${GCP_PROJECT_ID}" \
  --set-env-vars "FIRESTORE_DATABASE_ID=${FIRESTORE_DATABASE_ID}" \
  --set-env-vars "GCS_BUCKET_NAME=${GCS_BUCKET_NAME}" \
  --set-env-vars "SECRET_KEY=${SECRET_KEY}" \
  --set-env-vars "QR_CODE_BASE_URL=${QR_CODE_BASE_URL}" 
