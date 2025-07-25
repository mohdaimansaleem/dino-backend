#!/bin/bash
. .env.production.sh

gcloud builds submit . --tag ${CLOUD_RUN_IMAGE_NAME}
