#!/bin/bash
# Deploy MCP Server to Cloud Run with Public Access and OAuth

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT:-"your-project-id"}
SERVICE_NAME="mcp-server-public"
REGION=${GCP_REGION:-"us-central1"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# OAuth Configuration - Set these in your environment or replace
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-"your-client-id.apps.googleusercontent.com"}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-"your-client-secret"}
ALLOWED_DOMAINS=${ALLOWED_DOMAINS:-""}  # Optional: comma-separated domains

echo "Building and deploying MCP Server (Public with OAuth)..."
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"

# Build and push image
echo "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} .

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars="FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.google.GoogleProvider" \
    --set-env-vars="FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}" \
    --set-env-vars="FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}" \
    --set-env-vars="FASTMCP_SERVER_AUTH_GOOGLE_ALLOWED_DOMAINS=${ALLOWED_DOMAINS}" \
    --set-env-vars="VAC_CONFIG_FOLDER=/app/config" \
    --set-env-vars="GCP_PROJECT=${PROJECT_ID}" \
    --set-env-vars="GCP_REGION=${REGION}" \
    --set-env-vars="LOG_LEVEL=INFO" \
    --set-env-vars="SERVICE_MODE=public" \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --concurrency=100

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)')

# Update OAuth base URL
echo "Updating OAuth configuration with service URL..."
gcloud run services update ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --update-env-vars="FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL=${SERVICE_URL}"

echo ""
echo "✅ Deployment complete!"
echo "Service URL: ${SERVICE_URL}"
echo "MCP Endpoint: ${SERVICE_URL}/mcp"
echo ""
echo "⚠️  Important: Update your Google OAuth settings:"
echo "1. Go to https://console.cloud.google.com/apis/credentials"
echo "2. Edit your OAuth 2.0 Client ID"
echo "3. Add authorized redirect URI: ${SERVICE_URL}/auth/callback"
echo "4. Add authorized JavaScript origin: ${SERVICE_URL}"
echo ""
echo "Test with:"
echo "curl -X POST ${SERVICE_URL}/mcp/mcp \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/list\"}'"