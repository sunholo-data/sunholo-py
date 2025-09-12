---
id: fastapi-vac-routes
title: FastAPI VAC Routes
sidebar_label: FastAPI VAC Routes
---

# FastAPI VAC Routes

The `VACRoutesFastAPI` class provides a FastAPI-compatible implementation of VAC (Virtual Agent Computer) routes with full streaming support using callbacks. This enables you to build high-performance, async-first GenAI applications with proper streaming capabilities.

## Overview

VACRoutesFastAPI bridges the gap between callback-based LLM streaming (used by most LLM libraries) and FastAPI's async streaming responses. It supports:

- ✅ **Async and Sync Interpreters** - Automatic detection and handling
- ✅ **Multiple Streaming Formats** - Plain text and Server-Sent Events (SSE)
- ✅ **OpenAI API Compatibility** - Drop-in replacement for OpenAI endpoints
- ✅ **MCP Server Support** - Model Context Protocol for Claude Code integration
- ✅ **A2A Agent Support** - Agent-to-Agent communication protocol

## Installation

```bash
# Using uv (recommended)
uv pip install sunholo[fastapi]

# Or using pip
pip install sunholo[fastapi]
```

## Quick Start

### Basic Setup

```python
from fastapi import FastAPI
from sunholo.agents.fastapi import VACRoutesFastAPI

app = FastAPI()

# Define your interpreter function
async def my_stream_interpreter(
    question: str,
    vector_name: str,
    chat_history: list,
    callback: Any,
    **kwargs
) -> dict:
    """Your LLM logic here."""
    # Stream tokens via callback
    tokens = generate_tokens(question)  # Your LLM logic
    for token in tokens:
        await callback.async_on_llm_new_token(token)
    
    # Return final response
    final_response = {
        "answer": "".join(tokens),
        "source_documents": []
    }
    await callback.async_on_llm_end(final_response)
    return final_response

# Initialize VAC routes
vac_routes = VACRoutesFastAPI(
    app,
    stream_interpreter=my_stream_interpreter,
    enable_mcp_server=True  # Enable MCP for Claude Code
)

# Run with: uvicorn main:app --reload
```

## Callback Pattern

The key to VACRoutesFastAPI's streaming is the callback pattern. Your interpreter functions receive a callback object that handles token streaming:

### Async Interpreter with Callbacks

```python
async def async_stream_interpreter(
    question: str,
    vector_name: str,
    chat_history: list,
    callback: Any,  # Callback handler
    **kwargs
) -> dict:
    # Your LLM call that yields tokens
    async for token in llm.stream(question):
        # Send each token via callback
        await callback.async_on_llm_new_token(token)
    
    # Signal completion
    final_response = {"answer": full_text, "source_documents": sources}
    await callback.async_on_llm_end(final_response)
    return final_response
```

### Sync Interpreter with Callbacks

```python
def sync_stream_interpreter(
    question: str,
    vector_name: str,
    chat_history: list,
    callback: Any,
    **kwargs
) -> dict:
    # Sync LLM call
    for token in llm.stream(question):
        # Send each token via callback (sync version)
        callback.on_llm_new_token(token)
    
    # Signal completion
    final_response = {"answer": full_text, "source_documents": sources}
    callback.on_llm_end(final_response)
    return final_response
```

## Streaming Formats

### 1. Plain Text Streaming

Compatible with the Flask implementation, returns chunks as plain text:

```python
# Endpoint: POST /vac/streaming/{vector_name}
curl -X POST http://localhost:8000/vac/streaming/my_agent \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello!"}'

# Response: Streams text chunks, then final JSON with sources
Hello! How can I help you today?
{"answer": "Hello! How can I help you today?", "source_documents": [...]}
```

### 2. Server-Sent Events (SSE)

Better for browser-based clients, follows SSE format:

```python
# Endpoint: POST /vac/streaming/{vector_name}/sse
curl -X POST http://localhost:8000/vac/streaming/my_agent/sse \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello!"}'

# Response: SSE format
data: {"chunk": "Hello! "}
data: {"chunk": "How can I "}
data: {"chunk": "help you today?"}
data: {"answer": "Hello! How can I help you today?", "source_documents": [...]}
data: [DONE]
```

### JavaScript SSE Client Example

```javascript
async function streamChat(question, vectorName) {
    const response = await fetch(`/vac/streaming/${vectorName}/sse`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_input: question})
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                if (data.chunk) {
                    // Append streaming text
                    document.getElementById('output').textContent += data.chunk;
                }
            }
        }
    }
}
```

## OpenAI API Compatibility

VACRoutesFastAPI provides OpenAI-compatible endpoints:

```python
# Non-streaming
curl -X POST http://localhost:8000/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my_agent",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'

# Streaming
curl -X POST http://localhost:8000/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my_agent",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "stream": true
  }'
```

## Advanced Configuration

### Full Configuration Options

```python
from fastapi import FastAPI
from sunholo.agents.fastapi import VACRoutesFastAPI

app = FastAPI()

vac_routes = VACRoutesFastAPI(
    app,
    stream_interpreter=my_stream_interpreter,
    vac_interpreter=my_non_stream_interpreter,  # Optional non-streaming
    mcp_servers=[  # MCP client configuration
        {
            "name": "filesystem",
            "command": "mcp-server-filesystem",
            "args": ["/path/to/files"]
        }
    ],
    enable_mcp_server=True,      # Enable MCP server
    enable_a2a_agent=True,       # Enable A2A agent
    a2a_vac_names=["agent1", "agent2"],  # A2A agent names
    add_langfuse_eval=True       # Enable Langfuse tracing
)
```

### Custom Routes

Add your own custom routes alongside VAC routes:

```python
def create_custom_handler():
    async def custom_handler(request: Request):
        return JSONResponse({"message": "Custom endpoint"})
    return custom_handler

vac_routes = VACRoutesFastAPI(
    app,
    stream_interpreter=my_interpreter,
    additional_routes=[
        {
            "path": "/custom/endpoint",
            "handler": create_custom_handler(),
            "methods": ["GET", "POST"]
        }
    ]
)
```

## MCP Server Integration

Enable Model Context Protocol server for Claude Code integration:

```python
vac_routes = VACRoutesFastAPI(
    app,
    stream_interpreter=my_interpreter,
    enable_mcp_server=True
)

# MCP server available at:
# GET /mcp - Server information
# POST /mcp - Handle MCP requests
```

This allows Claude Code to interact with your VAC as an MCP tool.

## How It Works

### The Callback Bridge

VACRoutesFastAPI solves the callback-to-streaming challenge using these components:

1. **BufferStreamingStdOutCallbackHandlerAsync** - Receives tokens from the LLM
2. **ContentBuffer** - Thread-safe buffer with async event signaling
3. **Async Generator** - Yields content as it becomes available

```python
# Simplified flow
LLM → callback.on_llm_new_token() → ContentBuffer → async generator → StreamingResponse
```

### Sync/Async Handling

The class automatically detects whether your interpreter is async or sync:

- **Async interpreters**: Run directly with `await`
- **Sync interpreters**: Run in thread executor with queue-based communication

## Testing

### Running the Demo

Two demo options are available:

#### Standalone Demo (No Installation Required)
```bash
# Uses uv's inline dependencies - just run it!
uv run examples/fastapi_vac_demo_standalone.py

# Visit the interactive test page
open http://localhost:8000/test
```

#### Full Demo (With Sunholo Features)
```bash
# First install sunholo
uv pip install -e ".[fastapi]"

# Then run the demo
python examples/fastapi_vac_demo.py

# With sync interpreters
python examples/fastapi_vac_demo.py --sync
```

### Unit Testing

```bash
# Run the FastAPI VAC routes tests
uv run pytest tests/test_vac_routes_fastapi.py -v

# Run with coverage
uv run pytest tests/test_vac_routes_fastapi.py --cov=src/sunholo/agents/fastapi
```

Example test code:
```python
import pytest
from fastapi.testclient import TestClient
from sunholo.agents.fastapi import VACRoutesFastAPI

def test_streaming():
    app = FastAPI()
    vac_routes = VACRoutesFastAPI(app, stream_interpreter=my_interpreter)
    client = TestClient(app)
    
    response = client.post(
        "/vac/streaming/test",
        json={"user_input": "Hello"}
    )
    
    assert response.status_code == 200
    assert "Hello" in response.text
```

## Migration from Flask

If you're migrating from Flask VACRoutes:

### Flask Version
```python
from flask import Flask
from sunholo.agents.flask import VACRoutes

app = Flask(__name__)
vac_routes = VACRoutes(app, stream_interpreter, vac_interpreter)
```

### FastAPI Version
```python
from fastapi import FastAPI
from sunholo.agents.fastapi import VACRoutesFastAPI

app = FastAPI()
vac_routes = VACRoutesFastAPI(app, stream_interpreter, vac_interpreter)
```

The API is nearly identical - just change the import and class name!

## Best Practices

1. **Use Async When Possible** - Async interpreters provide better performance
2. **Handle Errors in Interpreters** - Wrap LLM calls in try/except blocks
3. **Set Appropriate Timeouts** - Configure `stream_timeout` based on your LLM
4. **Use SSE for Browsers** - SSE format works better with fetch() API
5. **Enable MCP for Development** - Makes debugging easier with Claude Code

## Troubleshooting

### Streaming Not Working

Check that your interpreter uses callbacks:
```python
# ✅ Correct - uses callback
async def interpreter(question, vector_name, chat_history, callback, **kwargs):
    await callback.async_on_llm_new_token("token")
    
# ❌ Wrong - no callback usage
async def interpreter(question, vector_name, chat_history, **kwargs):
    return {"answer": "response"}
```

### Sync Interpreter Issues

Ensure sync interpreters use the sync callback methods:
```python
# ✅ Correct for sync
callback.on_llm_new_token(token)

# ❌ Wrong for sync
await callback.async_on_llm_new_token(token)
```

### Archive QA Errors

The `archive_qa` function is synchronous. Don't use await:
```python
# ✅ Correct
archive_qa(bot_output, vector_name)

# ❌ Wrong - will cause "NoneType can't be used in await" error
await archive_qa(bot_output, vector_name)
```

### JavaScript Errors in Test Page

If you see "string literal contains an unescaped line break", ensure newlines are properly escaped in JavaScript strings within Python triple-quoted strings:
```python
# ✅ Correct - escaped newline
const lines = buffer.split('\\n');

# ❌ Wrong - will cause syntax error
const lines = buffer.split('\n');
```

### SSE Not Sending Final Response

Ensure your interpreter returns document objects with the correct format:
```python
# The source_documents should have page_content attribute
class MockDocument:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

final_response = {
    "answer": full_text,
    "source_documents": [
        MockDocument(
            page_content="Document content",
            metadata={"source": "file.txt"}
        )
    ]
}
```

### Timeout Errors

Increase the timeout in the request:
```python
response = client.post("/vac/streaming/agent", json={
    "user_input": "question",
    "stream_timeout": 120  # 2 minutes
})
```

## API Reference

### VACRoutesFastAPI

```python
class VACRoutesFastAPI:
    def __init__(
        self,
        app: FastAPI,
        stream_interpreter: Callable,
        vac_interpreter: Optional[Callable] = None,
        additional_routes: Optional[List[Dict]] = None,
        mcp_servers: Optional[List[Dict[str, Any]]] = None,
        add_langfuse_eval: bool = True,
        enable_mcp_server: bool = False,
        enable_a2a_agent: bool = False,
        a2a_vac_names: Optional[List[str]] = None
    )
```

### VACRequest Model

```python
class VACRequest(BaseModel):
    user_input: str
    chat_history: Optional[List] = None
    stream_wait_time: Optional[int] = 7
    stream_timeout: Optional[int] = 120
    vector_name: Optional[str] = None
    trace_id: Optional[str] = None
    eval_percent: Optional[float] = 0.01
```

## Endpoints Created

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home endpoint |
| `/health` | GET | Health check |
| `/vac/streaming/{vector_name}` | POST | Plain text streaming |
| `/vac/streaming/{vector_name}/sse` | POST | SSE streaming |
| `/vac/{vector_name}` | POST | Non-streaming response |
| `/openai/v1/chat/completions` | POST | OpenAI compatible |
| `/mcp` | GET/POST | MCP server (if enabled) |
| `/.well-known/agent.json` | GET | A2A agent card (if enabled) |

## Examples

Full working examples are available in:
- `examples/fastapi_vac_demo.py` - Complete demo with UI
- `tests/test_vac_routes_fastapi.py` - Unit tests
- `tests/fixtures/mock_interpreters.py` - Mock interpreters for testing