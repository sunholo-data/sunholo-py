# MCP Server for VACs

This guide explains how to expose your Sunholo VAC (Virtual Agent Computer) functionality as an MCP (Model Context Protocol) server, allowing it to be accessed by any MCP-compatible client.

## Overview

The MCP server functionality allows your Flask-based VAC application to serve as an MCP server, exposing your VAC's capabilities as tools that can be called via the MCP protocol. This is particularly useful when deploying to Google Cloud Run, where authentication is handled via IAM.

## Enabling MCP Server

To enable MCP server functionality in your VAC, set the `enable_mcp_server` parameter when initializing `VACRoutes`:

```python
from flask import Flask
from sunholo.agents.flask import VACRoutes

app = Flask(__name__)

vac_routes = VACRoutes(
    app,
    stream_interpreter=your_stream_interpreter,
    vac_interpreter=your_vac_interpreter,  # Optional
    enable_mcp_server=True  # Enable MCP server endpoint
)
```

This will create an MCP server endpoint at `/mcp` that handles HTTP-based JSON-RPC requests following the MCP protocol.

## Available MCP Tools

When MCP server is enabled, the following tools are exposed:

### vac_stream
Streams responses from a Sunholo VAC.

**Parameters:**
- `vector_name` (string, required): Name of the VAC to interact with
- `user_input` (string, required): The user's question or input
- `chat_history` (array, optional): Previous conversation history
- `stream_wait_time` (number, optional): Time to wait between stream chunks (default: 7)
- `stream_timeout` (number, optional): Maximum time to wait for response (default: 120)

### vac_query
Non-streaming query to a VAC (only available if `vac_interpreter` is provided).

**Parameters:**
- `vector_name` (string, required): Name of the VAC to interact with
- `user_input` (string, required): The user's question or input
- `chat_history` (array, optional): Previous conversation history

## Complete Example

```python
#!/usr/bin/env python3
from flask import Flask
from sunholo.agents.flask import VACRoutes

# Your custom interpreter functions
def my_stream_interpreter(question, vector_name, chat_history, **kwargs):
    """
    Streaming interpreter that yields responses.
    Replace with your actual VAC logic.
    """
    yield f"Processing query for VAC '{vector_name}': {question}\n"
    yield "Generating response...\n"
    yield {"answer": f"Final answer to: {question}"}

def my_vac_interpreter(question, vector_name, chat_history, **kwargs):
    """
    Non-streaming interpreter.
    Replace with your actual VAC logic.
    """
    return {
        "answer": f"Response from {vector_name}: {question}",
        "source_documents": []
    }

# Create Flask app
app = Flask(__name__)

# Initialize VAC routes with MCP server enabled
vac_routes = VACRoutes(
    app,
    stream_interpreter=my_stream_interpreter,
    vac_interpreter=my_vac_interpreter,
    enable_mcp_server=True
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

## Deploying to Google Cloud Run

The MCP server is designed to work seamlessly with Google Cloud Run's authentication:

1. Create a Dockerfile for your application:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Run the app
CMD ["python", "app.py"]
```

2. Build and push your container:
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/vac-mcp-server
```

3. Deploy to Cloud Run with authentication:
```bash
gcloud run deploy vac-mcp-server \
  --image gcr.io/YOUR_PROJECT/vac-mcp-server \
  --port 8080 \
  --no-allow-unauthenticated \
  --region us-central1
```

## Connecting MCP Clients

### Claude Desktop Integration

To use your VAC MCP server with Claude Desktop, you need to configure it in your Claude Desktop settings. Since Claude Desktop expects stdio-based communication, you'll need to use a stdio-to-HTTP bridge.

**1. Edit your Claude Desktop configuration file:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**2. Add your Sunholo VAC server configuration:**
```json
{
  "mcpServers": {
    "sunholo-vac": {
      "command": "sunholo",
      "args": [
        "mcp",
        "bridge",
        "http://127.0.0.1:1956/mcp"
      ]
    }
  }
}
```

Or if you prefer using `uv`:
```json
{
  "mcpServers": {
    "sunholo-vac": {
      "command": "uv",
      "args": [
        "run",
        "sunholo",
        "mcp",
        "bridge",
        "http://127.0.0.1:1956/mcp"
      ]
    }
  }
}
```

**3. For Cloud Run deployment:**
```json
{
  "mcpServers": {
    "sunholo-vac": {
      "command": "sunholo",
      "args": [
        "mcp",
        "bridge",
        "https://vac-mcp-server-xxxxx-uc.a.run.app/mcp"
      ]
    }
  }
}
```

**4. Restart Claude Desktop** to load the new configuration.

**5. Verify the integration:**
- Open Claude Desktop
- Check if your VAC tools (`vac_stream` and optionally `vac_query`) appear in the available tools
- Test by asking Claude to use the tools

### Claude Code Integration

For Claude Code (CLI), the configuration is different:

**1. Add your local MCP server:**
```bash
claude mcp add sunholo-vac sunholo mcp bridge http://127.0.0.1:1956/mcp
```

**2. For Cloud Run deployment:**
```bash
claude mcp add sunholo-vac sunholo mcp bridge https://vac-mcp-server-xxxxx-uc.a.run.app/mcp
```

**3. List configured MCP servers:**
```bash
claude mcp list
```

**4. Test the integration:**
```bash
claude mcp tools sunholo-vac
```

**5. Use in Claude Code:**
- Your VAC tools will appear as available MCP tools
- Use the tools directly: "Use the vac_stream tool with vector_name=my_vac and user_input=hello"
- Available tools: `vac_stream` (streaming) and `vac_query` (non-streaming)

**6. Remove if needed:**
```bash
claude mcp remove sunholo-vac
```

### Programming Client Integration

For programmatic access using MCP client SDK:

```python
# Example using MCP client SDK
from mcp.client import Client

# Connect to your Cloud Run MCP server
client = Client(
    url="https://vac-mcp-server-xxxxx-uc.a.run.app/mcp",
    auth_token=your_auth_token  # Cloud Run authentication
)

# List available tools
tools = await client.list_tools()

# Call the vac_stream tool
result = await client.call_tool(
    "vac_stream",
    {
        "vector_name": "my_vac",
        "user_input": "What is the weather today?",
        "chat_history": []
    }
)
```

## Authentication

When deployed to Cloud Run with `--no-allow-unauthenticated`, the MCP server is protected by Cloud Run's IAM authentication. Clients need:

1. The Cloud Run Invoker IAM role
2. Proper authentication tokens in their requests

For local development, you can use the Cloud Run proxy:
```bash
gcloud run services proxy vac-mcp-server --port=8080
```

Then connect to `http://localhost:8080/mcp`.

## Endpoint Details

The MCP server endpoint at `/mcp` supports:

- **GET**: Returns server information including available tools
- **POST**: Handles JSON-RPC requests following the MCP protocol

Example GET response:
```json
{
  "name": "sunholo-vac-server",
  "version": "1.0.0",
  "transport": "http",
  "endpoint": "/mcp",
  "tools": ["vac_stream", "vac_query"]
}
```

## Integration with Existing VAC Routes

The MCP server functionality integrates seamlessly with existing VAC routes:
- `/vac/streaming/<vector_name>` - Existing streaming endpoint
- `/vac/<vector_name>` - Existing static endpoint
- `/mcp` - New MCP server endpoint

All endpoints share the same interpreter functions, ensuring consistent behavior across different access methods.

## Testing Your MCP Server

You can test your MCP server directly using HTTP requests:

### Test Server Info
```bash
curl http://localhost:8080/mcp
```

Expected response:
```json
{
  "endpoint": "/mcp",
  "name": "sunholo-vac-server", 
  "tools": ["vac_stream", "vac_query"],
  "transport": "http",
  "version": "1.0.0"
}
```

### Test Tools List
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### Test Tool Execution
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/call",
    "params":{
      "name":"vac_stream",
      "arguments":{
        "vector_name":"test",
        "user_input":"Hello world",
        "stream_timeout":10
      }
    }
  }'
```

## Troubleshooting

### MCP server not enabled error
If you see "MCP server not enabled", ensure:
1. You've installed the required dependencies: `pip install sunholo[anthropic]`
2. You've set `enable_mcp_server=True` in VACRoutes initialization
3. The MCP dependencies are properly installed: `pip install mcp`

### "async for requires __aiter__ method" error
This indicates an async streaming issue. Ensure you've updated to the latest version with async queue fixes.

### Authentication errors on Cloud Run
Ensure the client has:
1. Cloud Run Invoker IAM role granted
2. Proper authentication headers in requests

### Connection timeouts
Adjust the `stream_timeout` parameter when calling the `vac_stream` tool if your VAC needs more processing time.

### Claude Desktop/Code not detecting MCP server
1. **For Claude Desktop:**
   - Check your configuration file location (see paths above)
   - Ensure you're using `@modelcontextprotocol/server-stdio-http` as the bridge
   - Restart Claude Desktop after configuration changes
   - Check that your VAC server is running on the specified port

2. **For Claude Code:**
   - Use `claude mcp list` to verify configuration
   - Test with `claude mcp tools sunholo-vac`
   - Ensure stdio-to-HTTP bridge is installed: `npm install -g @modelcontextprotocol/server-stdio-http`

### "Authentication required" error when running locally
This should not happen for local MCP servers. Check:
1. Your VAC server is running without authentication middleware for `/mcp` endpoint
2. No `_ENDPOINTS_HOST` environment variable is set
3. The authentication check in `check_authentication()` only applies to `/openai/` paths

### HTTP vs stdio transport confusion
- **Claude Desktop**: Requires stdio transport, use `sunholo mcp bridge` command
- **Direct HTTP clients**: Can connect directly to `http://localhost:1956/mcp`
- **Bridge command**: `sunholo mcp bridge [URL]` translates stdio to HTTP
- The bridge is built into Sunholo, no external npm packages needed

### Using the MCP Bridge

The `sunholo mcp bridge` command acts as a translator between stdio (what Claude Desktop expects) and HTTP (what your VAC server provides):

```bash
# Start the bridge manually (for testing)
sunholo mcp bridge http://127.0.0.1:1956/mcp

# Or with uv
uv run sunholo mcp bridge http://127.0.0.1:1956/mcp

# The bridge will forward stdio messages to your HTTP server
```

## See Also

- [Creating a VAC](creating_a_vac.md)
- [Flask App Development](flask_app.md)
- [MCP Integration Guide](mcp_integration.md)
- [Google Cloud Run MCP Documentation](https://cloud.google.com/run/docs/host-mcp-servers)