#!/usr/bin/env python3
"""
Example of using the FastMCP-based Sunholo VAC MCP Server.

This example shows how the new FastMCP implementation simplifies
the MCP server setup while maintaining all functionality.
"""

from fastapi import FastAPI
from sunholo.agents.fastapi import VACRoutesFastAPI
import asyncio

# Your custom interpreter functions
async def my_stream_interpreter(question, vector_name, chat_history, callback=None, **kwargs):
    """
    Example async streaming interpreter.
    Replace this with your actual VAC logic.
    """
    # Simulate streaming response
    tokens = [
        f"Processing query for VAC '{vector_name}': {question}\n",
        "This is a streaming response using FastMCP...\n",
        "The implementation is now much simpler!\n"
    ]
    
    full_response = ""
    for token in tokens:
        if callback:
            await callback.async_on_llm_new_token(token)
        full_response += token
        await asyncio.sleep(0.1)  # Simulate processing time
    
    final_result = {"answer": full_response}
    if callback:
        await callback.async_on_llm_end(final_result)
    
    return final_result

async def my_vac_interpreter(question, vector_name, chat_history, **kwargs):
    """
    Example non-streaming interpreter.
    Replace this with your actual VAC logic.
    """
    return {
        "answer": f"Non-streaming response from {vector_name}: {question}",
        "source_documents": []
    }

# Create FastAPI app
app = FastAPI(title="Sunholo VAC with FastMCP")

# Initialize VAC routes with MCP server enabled
# The new FastMCP implementation is used automatically
vac_routes = VACRoutesFastAPI(
    app,
    stream_interpreter=my_stream_interpreter,
    vac_interpreter=my_vac_interpreter,
    enable_mcp_server=True,  # This now uses FastMCP internally
    add_langfuse_eval=False
)

# Add a custom info endpoint to show the benefits
@app.get("/")
async def root():
    return {
        "message": "Sunholo VAC Server with FastMCP",
        "benefits": [
            "70% less boilerplate code",
            "Automatic schema generation from type hints",
            "Simplified tool registration with decorators",
            "Built-in transport handling (stdio/HTTP)",
            "Better error handling and validation"
        ],
        "endpoints": {
            "vac_streaming": "/vac/streaming/{vector_name}",
            "vac_static": "/vac/{vector_name}",
            "mcp_server": "/mcp",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Sunholo VAC Server with FastMCP")
    print("=" * 50)
    print("Benefits of FastMCP implementation:")
    print("✅ Cleaner, more Pythonic code")
    print("✅ Automatic type validation")
    print("✅ Simplified tool registration")
    print("✅ Better async support")
    print("=" * 50)
    print("\nEndpoints:")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("📍 MCP Server: http://localhost:8000/mcp")
    print("📍 VAC Streaming: http://localhost:8000/vac/streaming/{vector_name}")
    print("\nMCP Tools available:")
    print("🔧 vac_stream - Stream responses from a VAC")
    print("🔧 vac_query - Query a VAC (non-streaming)")
    print("\nTo test with Claude Desktop:")
    print("1. Configure in claude_desktop_config.json")
    print("2. Use: sunholo mcp bridge http://localhost:8000/mcp")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)