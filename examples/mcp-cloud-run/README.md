# MCP Server Cloud Run Deployment Examples

This directory contains examples for deploying Sunholo MCP servers to Google Cloud Run with different authentication strategies.

## Quick Start

### 1. Set up Google Cloud

```bash
# Set your project
export GCP_PROJECT=your-project-id
gcloud config set project $GCP_PROJECT

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Choose Your Deployment Strategy

#### Option A: Public with OAuth (External Users)

1. Create OAuth credentials in Google Cloud Console
2. Copy `.env.example` to `.env` and fill in OAuth credentials
3. Run deployment:
   ```bash
   chmod +x deploy-public.sh
   ./deploy-public.sh
   ```

#### Option B: Private with IAM (Internal Users)

1. Copy `.env.example` to `.env` and configure authorized users
2. Run deployment:
   ```bash
   chmod +x deploy-private.sh
   ./deploy-private.sh
   ```

## Files in this Directory

- `main.py` - FastAPI application with MCP server
- `Dockerfile` - Multi-stage Docker build for Cloud Run
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `deploy-public.sh` - Deploy script for public OAuth version
- `deploy-private.sh` - Deploy script for private IAM version

## Testing Your Deployment

### Test Public (OAuth) Service

1. Visit the service URL in your browser to trigger OAuth flow
2. Or use the provided curl commands after authentication

### Test Private (IAM) Service

```bash
# Get identity token
TOKEN=$(gcloud auth print-identity-token)

# Test MCP endpoint
curl -X POST https://your-service.a.run.app/mcp/mcp \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## Customization

### Adding Custom MCP Tools

Edit `main.py` and add your tools using the decorator:

```python
@vac_routes.add_mcp_tool
async def your_custom_tool(param1: str, param2: int) -> dict:
    """Your tool description."""
    # Implementation
    return {"result": "..."}
```

### Modifying the Stream Interpreter

Replace the `stream_interpreter` function in `main.py` with your actual VAC logic.

## Security Considerations

- **Public deployments**: Always configure OAuth domain restrictions
- **Private deployments**: Use least-privilege IAM bindings
- **Both**: Enable Cloud Monitoring and set up alerts
- **Secrets**: Use Secret Manager for sensitive values instead of environment variables

## Troubleshooting

See the main documentation at `/docs/mcp-cloud-run-deployment.md` for detailed troubleshooting steps.

## Support

For issues or questions, please refer to the [Sunholo documentation](https://dev.sunholo.com/) or create an issue in the repository.