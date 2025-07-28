#!/bin/bash
. .env.production.sh

gcloud firestore databases create \
--location=${GCP_REGION} \
--project=${GCP_PROJECT_ID} \
--database=${DATABASE_NAME} 