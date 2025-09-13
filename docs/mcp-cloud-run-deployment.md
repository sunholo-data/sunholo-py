# MCP Server Cloud Run Deployment Guide

This guide covers deploying Sunholo MCP servers to Google Cloud Run with different authentication strategies.

## Overview

When deploying MCP servers to Cloud Run, you have three authentication strategies depending on your use case:

1. **Public with OAuth** - For external users with Google OAuth protection
2. **Private with IAM** - For internal/service-to-service communication
3. **Hybrid** - Different endpoints with different auth requirements

## Authentication Strategies

### Strategy 1: Public Cloud Run with FastMCP OAuth

Best for: External users, browser-based access, Claude Desktop integration

#### Deployment

```bash
# Build and deploy
gcloud run deploy mcp-server-public \
    --source . \
    --allow-unauthenticated \
    --set-env-vars="FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.google.GoogleProvider" \
    --set-env-vars="FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}" \
    --set-env-vars="FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}" \
    --set-env-vars="FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL=https://mcp-server-public-xyz-uc.a.run.app" \
    --region=us-central1
```

#### OAuth Setup

1. Create OAuth 2.0 Client ID in Google Cloud Console:
   ```
   - Application type: Web application
   - Authorized redirect URIs: 
     - https://your-service-xyz-uc.a.run.app/auth/callback
   - Authorized JavaScript origins:
     - https://your-service-xyz-uc.a.run.app
   ```

2. (Optional) Restrict to domain:
   ```bash
   --set-env-vars="FASTMCP_SERVER_AUTH_GOOGLE_ALLOWED_DOMAINS=yourdomain.com"
   ```

#### Example Application

```python
from sunholo.agents.fastapi import VACRoutesFastAPI

# Create app with MCP and OAuth
app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
    title="Public MCP Server",
    stream_interpreter=my_interpreter,
    # OAuth is configured via environment variables
)
```

### Strategy 2: Private Cloud Run with IAM

Best for: Internal services, service accounts, programmatic access

#### Deployment

```bash
# Build and deploy (no --allow-unauthenticated flag)
gcloud run deploy mcp-server-private \
    --source . \
    --region=us-central1
    
# Grant access to specific users/service accounts
gcloud run services add-iam-policy-binding mcp-server-private \
    --member="user:developer@yourdomain.com" \
    --role="roles/run.invoker" \
    --region=us-central1
    
# Or for service accounts
gcloud run services add-iam-policy-binding mcp-server-private \
    --member="serviceAccount:my-service@project.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --region=us-central1
```

#### Client Authentication

```python
import google.auth
from google.auth.transport.requests import Request
import requests

# Get credentials and ID token
credentials, project = google.auth.default()
auth_req = Request()
credentials.refresh(auth_req)

# Make authenticated request
url = "https://mcp-server-private-xyz-uc.a.run.app/mcp"
headers = {"Authorization": f"Bearer {credentials.token}"}
response = requests.post(url, headers=headers, json={"method": "tools/list"})
```

### Strategy 3: Hybrid Deployment

Deploy separate services for different authentication needs:

#### Public Service (for browser/OAuth users)

```yaml
# public-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: mcp-server-public
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu: "1"
    spec:
      containers:
      - image: gcr.io/PROJECT/mcp-server:latest
        env:
        - name: FASTMCP_SERVER_AUTH
          value: "fastmcp.server.auth.providers.google.GoogleProvider"
        - name: FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: oauth-secrets
              key: client_id
        - name: FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: oauth-secrets
              key: client_secret
        - name: SERVICE_MODE
          value: "public"
```

#### Private Service (for internal/service accounts)

```yaml
# private-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: mcp-server-private
  annotations:
    run.googleapis.com/ingress: internal
spec:
  template:
    spec:
      containers:
      - image: gcr.io/PROJECT/mcp-server:latest
        env:
        - name: SERVICE_MODE
          value: "private"
```

## Configuration Examples

### Environment Variables Reference

```bash
# OAuth Configuration (Public deployments)
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.google.GoogleProvider
FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=your-client-secret
FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL=https://your-service.a.run.app
FASTMCP_SERVER_AUTH_GOOGLE_REDIRECT_PATH=/auth/callback  # Default
FASTMCP_SERVER_AUTH_GOOGLE_ALLOWED_DOMAINS=yourdomain.com,anotherdomain.com

# Service Configuration
VAC_CONFIG_FOLDER=/app/config
GCP_PROJECT=your-project-id
GCP_REGION=us-central1
LOG_LEVEL=INFO

# MCP Server Settings
MCP_SERVER_NAME=sunholo-vac-server
MCP_INCLUDE_VAC_TOOLS=true
```

### Dockerfile for Cloud Run

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Application Code Structure

```python
# main.py
import os
from sunholo.agents.fastapi import VACRoutesFastAPI

# Determine service mode
SERVICE_MODE = os.getenv("SERVICE_MODE", "public")

if SERVICE_MODE == "public":
    # Public service with OAuth
    app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
        title="Public MCP Server",
        stream_interpreter=stream_interpreter,
        # OAuth configured via env vars
    )
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "mode": "public", "auth": "oauth"}

else:
    # Private service with IAM
    app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
        title="Private MCP Server",
        stream_interpreter=stream_interpreter,
        # No OAuth needed, IAM handles auth
    )
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "mode": "private", "auth": "iam"}
```

## Security Best Practices

### For Public Deployments

1. **Domain Restrictions**: Always restrict OAuth to specific domains
2. **Rate Limiting**: Implement rate limiting at application level
3. **Cloud Armor**: Use Cloud Armor for DDoS protection
4. **Monitoring**: Set up Cloud Monitoring alerts for suspicious activity

```python
from fastapi import Request
from fastapi.middleware.throttling import ThrottlingMiddleware

app.add_middleware(
    ThrottlingMiddleware,
    rate_limit="100/minute"
)
```

### For Private Deployments

1. **Least Privilege**: Grant minimal IAM permissions
2. **Service Accounts**: Use dedicated service accounts
3. **VPC SC**: Consider VPC Service Controls for additional isolation
4. **Audit Logging**: Enable Cloud Audit Logs

```bash
# Create dedicated service account
gcloud iam service-accounts create mcp-client \
    --display-name="MCP Client Service Account"

# Grant only invoker permission
gcloud run services add-iam-policy-binding mcp-server-private \
    --member="serviceAccount:mcp-client@PROJECT.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

## Testing Deployments

### Test Public OAuth Service

```bash
# 1. Visit in browser to trigger OAuth flow
open https://mcp-server-public-xyz-uc.a.run.app/mcp

# 2. Or test with curl after obtaining token
curl -X POST https://mcp-server-public-xyz-uc.a.run.app/mcp/mcp \
    -H "Authorization: Bearer ${OAUTH_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### Test Private IAM Service

```bash
# Using gcloud to get identity token
TOKEN=$(gcloud auth print-identity-token)

curl -X POST https://mcp-server-private-xyz-uc.a.run.app/mcp/mcp \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## Troubleshooting

### Common Issues

1. **OAuth Redirect Loop**
   - Check `FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL` matches actual URL
   - Verify redirect URI in Google Console matches exactly

2. **403 Forbidden on Private Service**
   - Check IAM bindings: `gcloud run services get-iam-policy SERVICE_NAME`
   - Verify identity token is fresh (expires after 1 hour)

3. **CORS Issues**
   - Add CORS middleware for browser-based access:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://claude.ai"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

## Cost Optimization

- **Public Service**: Higher traffic, consider min instances for cold start reduction
- **Private Service**: Lower traffic, set min instances to 0
- **CPU Allocation**: Use CPU throttling for cost savings on non-latency-critical services

```bash
gcloud run deploy mcp-server \
    --cpu-throttling \
    --min-instances=0 \
    --max-instances=10 \
    --concurrency=100
```

## Next Steps

- Set up CI/CD pipeline for automated deployments
- Configure Cloud Monitoring dashboards
- Implement custom domain with Cloud Load Balancer
- Add Cloud CDN for static content caching