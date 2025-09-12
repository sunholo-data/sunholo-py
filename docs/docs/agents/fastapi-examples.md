# FastAPI VAC Routes Example

This directory contains a complete demonstration of the FastAPI VAC Routes implementation with streaming support.

## Quick Start

### Option 1: Standalone Demo (No Installation Required)

The standalone demo uses uv's inline script dependencies:

```bash
# Just run it - uv handles all dependencies automatically!
uv run examples/fastapi_vac_demo_standalone.py

# Custom port
uv run examples/fastapi_vac_demo_standalone.py --port 8080
```

### Option 2: Full Demo

The full demo requires sunholo to be installed:

```bash
# First install sunholo with FastAPI support
uv pip install -e ".[fastapi]"

# Then run with async interpreters (default)
python examples/fastapi_vac_demo.py

# Run with sync interpreters
python examples/fastapi_vac_demo.py --sync

# Custom port
python examples/fastapi_vac_demo.py --port 8080
```

### Testing Endpoints

Once the server is running, you can test it in multiple ways:

#### 1. Interactive Web UI

Open http://localhost:8000/test in your browser for an interactive testing interface.

#### 2. API Documentation

Visit http://localhost:8000/docs for auto-generated FastAPI documentation.

#### 3. Command Line Testing

```bash
# Plain text streaming
curl -X POST http://localhost:8000/vac/streaming/demo \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello, how are you?"}'

# Server-Sent Events (SSE) streaming
curl -X POST http://localhost:8000/vac/streaming/demo/sse \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Tell me a story"}'

# Non-streaming response
curl -X POST http://localhost:8000/vac/demo \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Quick question"}'

# OpenAI-compatible endpoint
curl -X POST http://localhost:8000/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "demo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

## Key Features Demonstrated

### 1. Callback-Based Streaming

The demo shows how to implement streaming with callbacks that work with FastAPI:

```python
async def stream_interpreter(question, vector_name, chat_history, callback, **kwargs):
    # Stream tokens via callback
    for token in generate_tokens():
        await callback.async_on_llm_new_token(token)
    
    # Signal completion
    await callback.async_on_llm_end(final_response)
```

### 2. Automatic Sync/Async Detection

The VACRoutesFastAPI class automatically detects whether your interpreter is async or sync and handles it appropriately.

### 3. Multiple Streaming Formats

- **Plain Text**: Compatible with Flask implementation
- **SSE (Server-Sent Events)**: Better for browser-based clients

### 4. OpenAI API Compatibility

Drop-in replacement for OpenAI's chat completion API, supporting both streaming and non-streaming modes.

## Architecture

```
Client Request
    ↓
FastAPI Route
    ↓
VACRoutesFastAPI
    ↓
Stream Interpreter (with callback)
    ↓
BufferStreamingStdOutCallbackHandlerAsync
    ↓
ContentBuffer (async event signaling)
    ↓
Async Generator
    ↓
StreamingResponse
    ↓
Client
```

## Files in This Example

- `fastapi_vac_demo.py` - Main demo script with mock interpreters
- `README_FASTAPI.md` - This file

## Related Files

- `src/sunholo/agents/fastapi/vac_routes.py` - Main implementation
- `tests/test_vac_routes_fastapi.py` - Unit tests
- `tests/fixtures/mock_interpreters.py` - Mock interpreters for testing
- `docs/docs/agents/fastapi-vac-routes.md` - Full documentation

## Integration with Real LLMs

To use with real LLMs, replace the mock interpreters with your actual implementation:

```python
from langchain.llms import OpenAI
from langchain.callbacks.base import BaseCallbackHandler

class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self, callback):
        self.callback = callback
    
    async def on_llm_new_token(self, token: str, **kwargs):
        await self.callback.async_on_llm_new_token(token)

async def real_stream_interpreter(question, vector_name, chat_history, callback, **kwargs):
    llm = OpenAI(streaming=True, callbacks=[StreamingCallbackHandler(callback)])
    response = await llm.agenerate([question])
    
    final_response = {
        "answer": response.generations[0][0].text,
        "source_documents": []  # Add your RAG sources here
    }
    
    await callback.async_on_llm_end(final_response)
    return final_response
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:
```bash
uv run python examples/fastapi_vac_demo.py --port 8001
```

### Dependencies Not Found

Make sure to install dependencies:
```bash
uv pip install fastapi uvicorn httpx
```

### Import Errors

The demo script adds the parent directory to the Python path. If you're running from a different location, adjust the path:
```python
import sys
import os
sys.path.insert(0, '/path/to/sunholo-py')
```

## Next Steps

1. Replace mock interpreters with real LLM implementations
2. Configure MCP server for Claude Code integration
3. Add authentication and rate limiting
4. Deploy to production with proper logging and monitoring

For more information, see the [full documentation](./fastapi-vac-routes.md).