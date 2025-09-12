# Sunholo Examples

This directory contains example implementations demonstrating various features of the Sunholo library.

## FastAPI VAC Routes Examples

### fastapi_vac_demo.py
Full-featured demo of the VACRoutesFastAPI implementation showing how to handle callback-based LLM streaming with FastAPI.

**Features:**
- ✅ Async and sync interpreter support
- ✅ SSE (Server-Sent Events) streaming
- ✅ Plain text streaming
- ✅ Interactive test page at `/test`
- ✅ OpenAI API compatibility
- ✅ MCP server integration
- ✅ Proper error handling and logging

**Run:**
```bash
# First install sunholo with FastAPI support
uv pip install -e ".[fastapi]"

# Run with async interpreters (default)
python examples/fastapi_vac_demo.py

# Run with sync interpreters
python examples/fastapi_vac_demo.py --sync

# Run on custom port
python examples/fastapi_vac_demo.py --port 8001
```

**Test:**
```bash
# Test SSE streaming
curl -X POST http://localhost:8000/vac/streaming/demo/sse \
    -H "Content-Type: application/json" \
    -d '{"user_input": "Tell me a story"}'

# Visit interactive test page
open http://localhost:8000/test
```

### fastapi_vac_demo_standalone.py
Standalone demo that doesn't require installing sunholo. Uses uv's inline script dependencies.

**Features:**
- ✅ Self-contained implementation
- ✅ No sunholo installation needed
- ✅ Simplified for learning/reference
- ✅ Same streaming capabilities as full demo

**Run:**
```bash
# Just run it - uv handles dependencies automatically
uv run examples/fastapi_vac_demo_standalone.py
```

## Key Implementation Notes

### Callback Pattern
Both demos show how to bridge the callback-based streaming pattern (used by LLM libraries) with FastAPI's async streaming responses:

```python
# LLM libraries use callbacks
await callback.async_on_llm_new_token(token)

# FastAPI uses async generators
async def generate():
    async for chunk in stream:
        yield f"data: {chunk}\n\n"
```

### Document Format
When implementing interpreters, ensure source documents have the correct format:

```python
class MockDocument:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata
```

### Common Issues Fixed
1. **Archive QA**: Don't use `await` on the sync `archive_qa()` function
2. **JavaScript Strings**: Escape newlines in JavaScript strings within Python triple-quoted strings (`'\\n'` not `'\n'`)
3. **Empty Yields**: Check for empty strings before yielding in streaming responses
4. **SSE Format**: Always end with `data: [DONE]\n\n` for proper SSE completion

## Other Examples

Additional examples will be added here demonstrating:
- Flask VAC Routes
- MCP server integration
- A2A agent communication
- Custom embedders and chunkers
- Vector store integrations
- Multi-agent configurations

## Documentation

For full documentation, see:
- [FastAPI VAC Routes Guide](../docs/docs/agents/fastapi-vac-routes.md)
- [Implementation Details](../docs/docs/agents/FASTAPI_IMPLEMENTATION_SUMMARY.md)
- [Fixes and Troubleshooting](../docs/docs/agents/FASTAPI_FIXES_SUMMARY.md)