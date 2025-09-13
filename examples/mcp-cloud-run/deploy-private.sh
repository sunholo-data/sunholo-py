#!/bin/bash
# Deploy MCP Server to Cloud Run with Private Access (IAM)

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT:-"your-project-id"}
SERVICE_NAME="mcp-server-private"
REGION=${GCP_REGION:-"us-central1"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# IAM Configuration - Users/service accounts to grant access
AUTHORIZED_USERS=${AUTHORIZED_USERS:-""}  # Comma-separated emails
AUTHORIZED_SERVICE_ACCOUNTS=${AUTHORIZED_SERVICE_ACCOUNTS:-""}  # Comma-separated service accounts

echo "Building and deploying MCP Server (Private with IAM)..."
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"

# Build and push image
echo "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} .

# Deploy to Cloud Run (without --allow-unauthenticated)
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --set-env-vars="VAC_CONFIG_FOLDER=/app/config" \
    --set-env-vars="GCP_PROJECT=${PROJECT_ID}" \
    --set-env-vars="GCP_REGION=${REGION}" \
    --set-env-vars="LOG_LEVEL=INFO" \
    --set-env-vars="SERVICE_MODE=private" \
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

# Grant IAM permissions to users
if [ -n "${AUTHORIZED_USERS}" ]; then
    echo "Granting access to users..."
    IFS=',' read -ra USERS <<< "${AUTHORIZED_USERS}"
    for user in "${USERS[@]}"; do
        user=$(echo "${user}" | xargs)  # Trim whitespace
        echo "  - ${user}"
        gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
            --member="user:${user}" \
            --role="roles/run.invoker" \
            --region=${REGION}
    done
fi

# Grant IAM permissions to service accounts
if [ -n "${AUTHORIZED_SERVICE_ACCOUNTS}" ]; then
    echo "Granting access to service accounts..."
    IFS=',' read -ra ACCOUNTS <<< "${AUTHORIZED_SERVICE_ACCOUNTS}"
    for account in "${ACCOUNTS[@]}"; do
        account=$(echo "${account}" | xargs)  # Trim whitespace
        echo "  - ${account}"
        gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
            --member="serviceAccount:${account}" \
            --role="roles/run.invoker" \
            --region=${REGION}
    done
fi

echo ""
echo "✅ Deployment complete!"
echo "Service URL: ${SERVICE_URL}"
echo "MCP Endpoint: ${SERVICE_URL}/mcp"
echo ""
echo "To test with your user account:"
echo "TOKEN=\$(gcloud auth print-identity-token)"
echo "curl -X POST ${SERVICE_URL}/mcp/mcp \\"
echo "  -H \"Authorization: Bearer \${TOKEN}\" \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/list\"}'"
echo ""
echo "To grant access to additional users:"
echo "gcloud run services add-iam-policy-binding ${SERVICE_NAME} \\"
echo "  --member='user:email@domain.com' \\"
echo "  --role='roles/run.invoker' \\"
echo "  --region=${REGION}"