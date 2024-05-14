#!/bin/bash

# Stop execution if any command fails
set -e

# Define project and app names
project_name="smartfile-422907"
build_name="smartfile_build_10"
gcloud_run_service_name="smartfile-dev"


# Use project and app names in commands
docker_image_tag="gcr.io/$project_name/$build_name:latest"
gcloud_run_region="us-central1"

# Build the Docker image
echo "Building Docker image..."
# docker build -t gcr.io/smartfile-422907/smartfile_build_10 .
# docker buildx build --platform linux/amd64 -t $docker_image_tag . 
gcloud builds submit --tag $docker_image_tag


# Push the image to Google Container Registry
echo "Pushing image to GCR..."
# docker push $docker_image_tag

# Deploy to Google Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $gcloud_run_service_name --image $docker_image_tag
    # --region $gcloud_run_region \
    # --set-secrets=/app/smartfile-account.json=firebase-admin-service-account:latest
    # --set-secrets=GROQ_API_KEY=API-Keys_langchain_llms:latest,LANGSMITH_API_KEY=API-Keys_langchain_llms:latest,LANGCHAIN_API_KEY=API-Keys_langchain_llms:latest,OPENAI_API_KEY=API-Keys_langchain_llms:latest,
# terminated: Application failed to start: "uvicorn main:app --host 0.0.0.0 --port 8080" not found (PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin)
# OPENROUTER_API_KEY=
# GROQ_API_KEY=
# LANGSMITH_API_KEY=
# LANGCHAIN_TRACING_V2=
# LANGCHAIN_API_KEY=
# OPENAI_API_KEY=

echo "Deployment successful!"
