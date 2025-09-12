#!/usr/bin/env python3
"""
Simple FastAPI VAC with MCP Server Example

This example shows the easiest way to set up a FastAPI app with VAC routes
and MCP server support using the simplified helper method.

Run this with:
    python examples/fastapi_vac_mcp_simple.py

Then test with:
    # Check MCP server
    curl -X POST http://localhost:8000/mcp \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
    
    # Use VAC endpoint
    curl -X POST http://localhost:8000/vac/streaming/demo \
        -H "Content-Type: application/json" \
        -d '{"user_input": "Hello!"}'
"""

from sunholo.agents.fastapi import VACRoutesFastAPI
import uvicorn


async def my_stream_interpreter(question, vector_name, chat_history, callback, **kwargs):
    """Simple streaming interpreter that echoes the input."""
    response = f"Echo from {vector_name}: {question}"
    
    # Stream tokens if callback provided
    if callback:
        for word in response.split():
            if hasattr(callback, 'async_on_llm_new_token'):
                await callback.async_on_llm_new_token(word + " ")
            elif hasattr(callback, 'on_llm_new_token'):
                callback.on_llm_new_token(word + " ")
    
    return {
        "answer": response,
        "source_documents": []
    }


# One line to set up everything with MCP server and proper lifespan management!
# MCP is automatically enabled when using create_app_with_mcp
app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
    title="Simple VAC with MCP",
    stream_interpreter=my_stream_interpreter
)


# Add any custom endpoints
@app.get("/custom")
async def custom_endpoint():
    return {"message": "This is a custom endpoint"}


# Add custom MCP tools
@vac_routes.add_mcp_tool
async def reverse_text(text: str) -> str:
    """Reverse the input text."""
    return text[::-1]


# For custom name/description, register after definition
async def make_uppercase(text: str) -> str:
    """Make text uppercase and loud!"""
    return text.upper()

vac_routes.add_mcp_tool(make_uppercase, name="shout")


if __name__ == "__main__":
    print("Starting Simple VAC with MCP Server...")
    print("MCP server available at: http://localhost:8000/mcp")
    print("VAC streaming at: http://localhost:8000/vac/streaming/{vector_name}")
    print("\nTest MCP tools list:")
    print('  curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d \'{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}\'')
    
    uvicorn.run(app, host="0.0.0.0", port=8000)