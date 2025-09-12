#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "fastapi",
#     "uvicorn",
#     "httpx",
# ]
# ///
"""
Standalone FastAPI VAC Routes Demonstration Script

This is a simplified standalone version that demonstrates the VACRoutesFastAPI
pattern without requiring the full sunholo package installation.

Run this script with:
    uv run examples/fastapi_vac_demo_standalone.py

Then test with:
    # Browser test page
    open http://localhost:8000/test
    
    # Plain text streaming
    curl -X POST http://localhost:8000/vac/streaming/demo \
        -H "Content-Type: application/json" \
        -d '{"user_input": "Hello, how are you?"}'
    
    # SSE streaming
    curl -X POST http://localhost:8000/vac/streaming/demo/sse \
        -H "Content-Type: application/json" \
        -d '{"user_input": "Tell me a story"}'
"""

import asyncio
import json
import logging
import time
from typing import Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request model
class VACRequest(BaseModel):
    """Request model for VAC endpoints."""
    user_input: str
    chat_history: Optional[List] = None
    stream_wait_time: Optional[int] = 7
    stream_timeout: Optional[int] = 120


# Demo Async Stream Interpreter
async def demo_async_stream_interpreter(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    callback: Any = None,
    **kwargs
) -> dict:
    """Demo async interpreter that simulates streaming."""
    logger.info(f"Async Stream for '{vector_name}': {question}")
    
    response_parts = [
        "Hello! ", "I'm ", "streaming ", "your ", "response. ",
        "You asked: ", f'"{question}". ',
        "This ", "demonstrates ", "async ", "streaming!"
    ]
    
    for token in response_parts:
        if callback and hasattr(callback, 'on_token'):
            await callback.on_token(token)
        await asyncio.sleep(0.1)
    
    full_answer = "".join(response_parts)
    return {
        "answer": full_answer,
        "source_documents": [
            {"content": "Demo source", "metadata": {"source": "demo.txt"}}
        ]
    }


# Simplified callback handler
class SimpleCallback:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
    
    async def on_token(self, token: str):
        await self.queue.put(token)


# Simplified VAC Routes
class SimpleVACRoutes:
    def __init__(self, app: FastAPI, stream_interpreter):
        self.app = app
        self.stream_interpreter = stream_interpreter
        self.register_routes()
    
    def register_routes(self):
        self.app.get("/")(self.home)
        self.app.get("/health")(self.health)
        self.app.get("/test", response_class=HTMLResponse)(self.test_page)
        self.app.post("/vac/streaming/{vector_name}")(self.stream_plain)
        self.app.post("/vac/streaming/{vector_name}/sse")(self.stream_sse)
    
    async def home(self):
        return JSONResponse(content={"message": "VAC Routes Demo"})
    
    async def health(self):
        return JSONResponse(content={"status": "healthy"})
    
    async def stream_plain(self, vector_name: str, request: VACRequest):
        """Plain text streaming endpoint."""
        async def generate():
            queue = asyncio.Queue()
            callback = SimpleCallback(queue)
            
            # Start interpreter in background
            task = asyncio.create_task(
                self.stream_interpreter(
                    request.user_input,
                    vector_name,
                    request.chat_history or [],
                    callback
                )
            )
            
            # Stream tokens as they arrive
            while not task.done():
                try:
                    token = await asyncio.wait_for(queue.get(), timeout=0.5)
                    yield token
                except asyncio.TimeoutError:
                    continue
            
            # Get final result
            result = await task
            yield "\n" + json.dumps(result)
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    async def stream_sse(self, vector_name: str, request: VACRequest):
        """Server-Sent Events streaming endpoint."""
        async def generate_sse():
            queue = asyncio.Queue()
            callback = SimpleCallback(queue)
            
            task = asyncio.create_task(
                self.stream_interpreter(
                    request.user_input,
                    vector_name,
                    request.chat_history or [],
                    callback
                )
            )
            
            # Stream tokens as SSE
            while not task.done():
                try:
                    token = await asyncio.wait_for(queue.get(), timeout=0.5)
                    yield f"data: {json.dumps({'chunk': token})}\n\n"
                except asyncio.TimeoutError:
                    continue
            
            # Get the final result and send it
            result = await task
            yield f"data: {json.dumps(result)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_sse(), 
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Disable proxy buffering
            }
        )
    
    async def test_page(self):
        """Interactive test page."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>VAC Streaming Test</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .container { display: flex; gap: 20px; }
        .section { flex: 1; }
        input { width: 100%; padding: 10px; margin: 10px 0; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .response { border: 1px solid #ddd; padding: 15px; min-height: 200px; background: #f9f9f9; white-space: pre-wrap; }
        .streaming { background: #e8f5e9; }
    </style>
</head>
<body>
    <h1>VAC FastAPI Streaming Test</h1>
    
    <div class="container">
        <div class="section">
            <h2>Plain Text Streaming</h2>
            <input type="text" id="question1" value="Tell me about streaming" placeholder="Enter your question" />
            <button onclick="testPlain()">Test Plain Streaming</button>
            <div id="response1" class="response"></div>
        </div>
        
        <div class="section">
            <h2>SSE Streaming</h2>
            <input type="text" id="question2" value="How does SSE work?" placeholder="Enter your question" />
            <button onclick="testSSE()">Test SSE Streaming</button>
            <div id="response2" class="response"></div>
        </div>
    </div>
    
    <script>
        async function testPlain() {
            const responseDiv = document.getElementById('response1');
            const question = document.getElementById('question1').value;
            
            responseDiv.textContent = 'Streaming...';
            responseDiv.className = 'response streaming';
            
            const response = await fetch('/vac/streaming/demo', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_input: question})
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let text = '';
            
            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                text += chunk;
                responseDiv.textContent = text;
            }
            responseDiv.className = 'response';
        }
        
        async function testSSE() {
            const responseDiv = document.getElementById('response2');
            const question = document.getElementById('question2').value;
            
            responseDiv.textContent = '';
            responseDiv.className = 'response streaming';
            
            const response = await fetch('/vac/streaming/demo/sse', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_input: question})
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let text = '';
            
            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value);
                const lines = buffer.split('\\n');
                buffer = lines.pop();
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            responseDiv.className = 'response';
                        } else {
                            try {
                                const json = JSON.parse(data);
                                if (json.chunk) {
                                    text += json.chunk;
                                    responseDiv.textContent = text;
                                } else if (json.answer) {
                                    responseDiv.innerHTML = '<b>Answer:</b>\\n' + json.answer +
                                        '\\n\\n<b>Sources:</b>\\n' + JSON.stringify(json.source_documents, null, 2);
                                }
                            } catch (e) {}
                        }
                    }
                }
            }
        }
    </script>
</body>
</html>
        """


def main():
    """Main function to run the demo server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Standalone VAC Routes Demo")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()
    
    # Create app
    app = FastAPI(title="VAC Routes Demo")
    
    # Initialize routes
    vac_routes = SimpleVACRoutes(app, demo_async_stream_interpreter)
    
    # Print info
    print("\n" + "="*60)
    print("Standalone VAC Routes FastAPI Demo")
    print("="*60)
    print(f"Server URL: http://localhost:{args.port}")
    print(f"Test Page: http://localhost:{args.port}/test")
    print(f"API Docs: http://localhost:{args.port}/docs")
    print("="*60 + "\n")
    
    # Run server
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()