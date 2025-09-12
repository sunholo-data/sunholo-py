#!/usr/bin/env python3
"""
FastAPI VAC Routes Demonstration Script

This script demonstrates how to use the VACRoutesFastAPI class with both
async and sync interpreters, including streaming and non-streaming endpoints.

Prerequisites:
    uv pip install -e ".[fastapi]"

Run this script with:
    python examples/fastapi_vac_demo.py

Then test with:
    # Plain text streaming
    curl -X POST http://localhost:8000/vac/streaming/demo \
        -H "Content-Type: application/json" \
        -d '{"user_input": "Hello, how are you?"}'
    
    # SSE streaming
    curl -X POST http://localhost:8000/vac/streaming/demo/sse \
        -H "Content-Type: application/json" \
        -d '{"user_input": "Tell me a story"}'
    
    # Non-streaming
    curl -X POST http://localhost:8000/vac/demo \
        -H "Content-Type: application/json" \
        -d '{"user_input": "What is the weather?"}'
    
    # OpenAI compatible
    curl -X POST http://localhost:8000/openai/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{
            "model": "demo",
            "messages": [{"role": "user", "content": "Hello!"}],
            "stream": true
        }'
"""

import asyncio
import logging
import os
import sys
import time
from typing import Any, List, Optional

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

# Add parent directory to path to import sunholo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.sunholo.agents.fastapi.vac_routes import VACRoutesFastAPI


# Demo Async Stream Interpreter
async def demo_async_stream_interpreter(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    callback: Any = None,
    **kwargs
) -> dict:
    """
    Demo async interpreter that simulates an LLM streaming response.
    This mimics how a real LLM (like OpenAI or Anthropic) would stream tokens.
    """
    logger.info(f"Async Stream Interpreter called for '{vector_name}' with question: {question}")
    logger.info(f"Callback type: {type(callback)}")
    
    # Simulate streaming response
    response_parts = [
        "Hello! ",
        "I'm ",
        "a demo ",
        "async ",
        "streaming ",
        "interpreter. ",
        "\n\n",
        "You asked: ",
        f'"{question}". ',
        "\n\n",
        "Here's ",
        "my ",
        "streaming ",
        "response ",
        "with ",
        "simulated ",
        "token ",
        "delays. ",
        "This ",
        "demonstrates ",
        "how ",
        "the ",
        "callback ",
        "pattern ",
        "works ",
        "with ",
        "FastAPI ",
        "streaming!"
    ]
    
    # Stream tokens via callback
    for token in response_parts:
        if callback:
            if hasattr(callback, 'async_on_llm_new_token'):
                await callback.async_on_llm_new_token(token)
            elif hasattr(callback, 'on_llm_new_token'):
                callback.on_llm_new_token(token)
        
        # Simulate processing delay
        await asyncio.sleep(0.1)
    
    # IMPORTANT: Final response with sources - this MUST be returned for streaming to complete
    full_answer = "".join(response_parts)
    
    # Create mock document objects that parse_output expects
    class MockDocument:
        def __init__(self, page_content, metadata):
            self.page_content = page_content
            self.metadata = metadata
    
    final_response = {
        "answer": full_answer,
        "source_documents": [
            MockDocument(
                page_content="This is a demo source document showing how sources are returned.",
                metadata={
                    "source": "demo_source.txt",
                    "page": 1,
                    "relevance_score": 0.95
                }
            ),
            MockDocument(
                page_content="Another example source with relevant information.",
                metadata={
                    "source": "demo_knowledge_base.md",
                    "page": 3,
                    "relevance_score": 0.87
                }
            )
        ]
    }
    
    # Signal completion
    if callback:
        if hasattr(callback, 'async_on_llm_end'):
            logger.info("Calling async_on_llm_end with final response")
            await callback.async_on_llm_end(final_response)
        elif hasattr(callback, 'on_llm_end'):
            logger.info("Calling on_llm_end with final response")
            callback.on_llm_end(final_response)
    
    logger.info(f"Returning final response: {list(final_response.keys())}")
    return final_response


# Demo Sync Stream Interpreter
def demo_sync_stream_interpreter(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    callback: Any = None,
    **kwargs
) -> dict:
    """
    Demo sync interpreter that simulates a synchronous LLM streaming response.
    This shows how sync interpreters are handled by VACRoutesFastAPI.
    """
    logger.info(f"Sync Stream Interpreter called for '{vector_name}' with question: {question}")
    
    # Simulate streaming response
    response_parts = [
        "Greetings! ",
        "This ",
        "is ",
        "the ",
        "SYNC ",
        "interpreter ",
        "responding. ",
        f"Your question was: '{question}'. ",
        "Even ",
        "though ",
        "I'm ",
        "synchronous, ",
        "FastAPI ",
        "handles ",
        "me ",
        "properly!"
    ]
    
    # Stream tokens via callback
    for token in response_parts:
        if callback and hasattr(callback, 'on_llm_new_token'):
            callback.on_llm_new_token(token)
        
        # Simulate processing delay
        time.sleep(0.05)
    
    # Final response
    full_answer = "".join(response_parts)
    
    # Create mock document objects that parse_output expects
    class MockDocument:
        def __init__(self, page_content, metadata):
            self.page_content = page_content
            self.metadata = metadata
    
    final_response = {
        "answer": full_answer,
        "source_documents": [
            MockDocument(
                page_content="Sync interpreter source document.",
                metadata={"source": "sync_source.txt"}
            )
        ]
    }
    
    # Signal completion
    if callback and hasattr(callback, 'on_llm_end'):
        callback.on_llm_end(final_response)
    
    return final_response


# Demo Non-streaming Interpreter
async def demo_vac_interpreter(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    **kwargs
) -> dict:
    """
    Demo non-streaming interpreter for quick responses.
    """
    logger.info(f"VAC Interpreter (non-streaming) called for '{vector_name}' with question: {question}")
    
    # Simulate some processing
    await asyncio.sleep(0.5)
    
    return {
        "answer": f"Non-streaming response to: '{question}'. This is a complete response returned all at once.",
        "source_documents": [
            {
                "page_content": "Non-streaming source content.",
                "metadata": {"source": "vac_source.json", "timestamp": "2024-01-15"}
            }
        ]
    }


# Create Demo Application
def create_demo_app(use_async: bool = True):
    """
    Create a demo FastAPI application with VACRoutesFastAPI.
    
    Args:
        use_async: If True, use async interpreters; if False, use sync interpreters
    """
    # Choose interpreters based on use_async flag
    if use_async:
        stream_interpreter = demo_async_stream_interpreter
        vac_interpreter = demo_vac_interpreter
        logger.info("Using ASYNC interpreters")
    else:
        stream_interpreter = demo_sync_stream_interpreter
        # For sync demo, create a sync version of vac_interpreter
        def sync_vac_interpreter(question, vector_name, chat_history=None, **kwargs):
            time.sleep(0.5)
            return {
                "answer": f"Sync non-streaming response to: '{question}'",
                "source_documents": []
            }
        vac_interpreter = sync_vac_interpreter
        logger.info("Using SYNC interpreters")
    
    # Define app lifespan (could include startup/shutdown logic)
    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        # Startup
        logger.info("Starting up demo app...")
        yield
        # Shutdown
        logger.info("Shutting down demo app...")
    
    # Use the simplified helper method for automatic lifespan management
    # MCP server is automatically enabled when using create_app_with_mcp
    app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
        title="VAC Routes FastAPI Demo",
        stream_interpreter=stream_interpreter,
        vac_interpreter=vac_interpreter,
        app_lifespan=app_lifespan,  # Optional: include your app's lifespan
        enable_a2a_agent=False,      # Disable A2A for this demo
        add_langfuse_eval=False      # Disable Langfuse for this demo
    )
    
    # Add description to the app
    app.description = "Demonstration of VACRoutesFastAPI with streaming support"
    app.version = "1.0.0"
    
    # Add a custom info endpoint
    @app.get("/info")
    async def info():
        return {
            "message": "VAC Routes FastAPI Demo",
            "interpreter_type": "async" if use_async else "sync",
            "endpoints": [
                "GET /",
                "GET /health",
                "GET /info",
                "GET /docs",
                "POST /vac/streaming/{vector_name}",
                "POST /vac/streaming/{vector_name}/sse",
                "POST /vac/{vector_name}",
                "POST /openai/v1/chat/completions",
                "GET /mcp (MCP server info)",
                "POST /mcp (MCP server requests)"
            ],
            "test_commands": {
                "streaming": 'curl -X POST http://localhost:8000/vac/streaming/demo -H "Content-Type: application/json" -d \'{"user_input": "Hello!"}\'',
                "sse": 'curl -X POST http://localhost:8000/vac/streaming/demo/sse -H "Content-Type: application/json" -d \'{"user_input": "Hello!"}\'',
                "non_streaming": 'curl -X POST http://localhost:8000/vac/demo -H "Content-Type: application/json" -d \'{"user_input": "Hello!"}\'',
                "openai": 'curl -X POST http://localhost:8000/openai/v1/chat/completions -H "Content-Type: application/json" -d \'{"model": "demo", "messages": [{"role": "user", "content": "Hello!"}], "stream": true}\''
            }
        }
    
    return app


# HTML Test Page
def create_test_page():
    """Create an HTML page for testing streaming in the browser."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>VAC FastAPI Streaming Test 2</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .container { display: flex; gap: 20px; }
        .section { flex: 1; }
        h1 { color: #333; }
        .input-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 10px; font-size: 16px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; font-size: 16px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .response { border: 1px solid #ddd; padding: 15px; min-height: 200px; background: #f9f9f9; white-space: pre-wrap; }
        .streaming { background: #e8f5e9; }
        .error { background: #ffebee; color: #c62828; }
        .source { background: #fff3e0; padding: 10px; margin-top: 10px; border-left: 3px solid #ff9800; }
    </style>
</head>
<body>
    <h1>VAC FastAPI Streaming Test</h1>
    
    <div class="container">
        <div class="section">
            <h2>Plain Text Streaming</h2>
            <div class="input-group">
                <label>Vector Name:</label>
                <input type="text" id="vectorName1" value="demo" />
            </div>
            <div class="input-group">
                <label>Question:</label>
                <input type="text" id="question1" value="Tell me about streaming" placeholder="Enter your question" />
            </div>
            <button onclick="testPlainStreaming()">Test Plain Streaming</button>
            <h3>Response:</h3>
            <div id="response1" class="response"></div>
        </div>
        
        <div class="section">
            <h2>SSE Streaming</h2>
            <div class="input-group">
                <label>Vector Name:</label>
                <input type="text" id="vectorName2" value="demo" />
            </div>
            <div class="input-group">
                <label>Question:</label>
                <input type="text" id="question2" value="How does SSE work?" placeholder="Enter your question" />
            </div>
            <button onclick="testSSEStreaming()">Test SSE Streaming</button>
            <h3>Response:</h3>
            <div id="response2" class="response"></div>
        </div>
    </div>
    
    <script>
        async function testPlainStreaming() {
            const responseDiv = document.getElementById('response1');
            const vectorName = document.getElementById('vectorName1').value;
            const question = document.getElementById('question1').value;
            
            responseDiv.textContent = 'Streaming...';
            responseDiv.className = 'response streaming';
            
            try {
                const response = await fetch(`/vac/streaming/${vectorName}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_input: question,
                        stream_wait_time: 1,
                        stream_timeout: 30
                    })
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullText = '';
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, {stream: true});
                    fullText += chunk;
                    
                    // Try to parse as JSON for final response
                    try {
                        const json = JSON.parse(fullText);
                        if (json.answer) {
                            responseDiv.innerHTML = '<strong>Answer:</strong><br>' + json.answer;
                            if (json.source_documents) {
                                responseDiv.innerHTML += '<br><br><strong>Sources:</strong>';
                                json.source_documents.forEach(doc => {
                                    responseDiv.innerHTML += `<div class="source">${JSON.stringify(doc, null, 2)}</div>`;
                                });
                            }
                        }
                    } catch {
                        // Not JSON yet, show raw text
                        responseDiv.textContent = fullText;
                    }
                }
                
                responseDiv.className = 'response';
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.className = 'response error';
            }
        }
        
        async function testSSEStreaming() {
            const responseDiv = document.getElementById('response2');
            const vectorName = document.getElementById('vectorName2').value;
            const question = document.getElementById('question2').value;
            
            responseDiv.textContent = '';
            responseDiv.className = 'response streaming';
            
            try {
                const response = await fetch(`/vac/streaming/${vectorName}/sse`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_input: question,
                        stream_wait_time: 1,
                        stream_timeout: 30
                    })
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let fullText = '';
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, {stream: true});
                    const lines = buffer.split('\\n');
                    buffer = lines.pop(); // Keep incomplete line in buffer
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            if (data === '[DONE]') {
                                responseDiv.className = 'response';
                                responseDiv.innerHTML += '<div style="color: green; margin-top: 10px;">✓ Stream completed successfully (received [DONE] signal)</div>';
                                continue;
                            }
                            
                            try {
                                const json = JSON.parse(data);
                                if (json.chunk) {
                                    fullText += json.chunk;
                                    responseDiv.textContent = fullText;
                                } else if (json.answer) {
                                    responseDiv.innerHTML = '<strong>Answer:</strong><br>' + json.answer;
                                    if (json.source_documents) {
                                        responseDiv.innerHTML += '<br><br><strong>Sources:</strong>';
                                        json.source_documents.forEach(doc => {
                                            responseDiv.innerHTML += `<div class="source">${JSON.stringify(doc, null, 2)}</div>`;
                                        });
                                    }
                                }
                            } catch (e) {
                                console.error('Parse error:', e, data);
                            }
                        }
                    }
                }
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.className = 'response error';
            }
        }
    </script>
</body>
</html>
    """


def main():
    """Main function to run the demo server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VAC Routes FastAPI Demo")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Use synchronous interpreters instead of async"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Create the demo app
    app = create_demo_app(use_async=not args.sync)
    
    # Add HTML test page
    @app.get("/test", response_class=HTMLResponse)
    async def test_page():
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=create_test_page())
    
    # Print startup information
    print("\n" + "="*60)
    print("VAC Routes FastAPI Demo Server")
    print("="*60)
    print(f"Interpreter Type: {'SYNC' if args.sync else 'ASYNC'}")
    print(f"Server URL: http://{args.host}:{args.port}")
    print("\nEndpoints:")
    print(f"  - Interactive Test Page: http://localhost:{args.port}/test")
    print(f"  - API Documentation: http://localhost:{args.port}/docs")
    print(f"  - Server Info: http://localhost:{args.port}/info")
    print("\nTest Commands:")
    print("  # Plain text streaming:")
    print(f'  curl -X POST http://localhost:{args.port}/vac/streaming/demo \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"user_input": "Hello, how are you?"}\'')
    print("\n  # SSE streaming:")
    print(f'  curl -X POST http://localhost:{args.port}/vac/streaming/demo/sse \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"user_input": "Tell me a story"}\'')
    print("\n" + "="*60 + "\n")
    
    # Run the server
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()