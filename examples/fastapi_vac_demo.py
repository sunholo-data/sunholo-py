#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "sunholo[http,anthropic]>=0.144.8",
#     "uvicorn",
# ]
# ///
"""
FastAPI VAC Routes Demonstration Script

This script demonstrates how to use the VACRoutesFastAPI class with both
async and sync interpreters, including streaming and non-streaming endpoints.

Run this script with uv (dependencies are auto-installed):
    uv run examples/fastapi_vac_demo.py
    
Or make it executable and run directly:
    chmod +x examples/fastapi_vac_demo.py
    ./examples/fastapi_vac_demo.py

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
    
    # Add simple demo MCP tools that work without complex dependencies
    @vac_routes.add_mcp_tool
    async def demo_reverse_text(text: str) -> str:
        """Reverse the input text as a demo."""
        return text[::-1]
    
    @vac_routes.add_mcp_tool
    async def demo_uppercase(text: str) -> str:
        """Convert text to uppercase as a demo."""
        return text.upper()
    
    @vac_routes.add_mcp_tool
    async def demo_echo(message: str, count: int = 1) -> str:
        """Echo a message multiple times."""
        return " ".join([message] * count)
    
    @vac_routes.add_mcp_tool
    async def demo_word_count(text: str) -> dict:
        """Count words and characters in text."""
        words = text.split()
        return {
            "word_count": len(words),
            "char_count": len(text),
            "char_count_no_spaces": len(text.replace(" ", ""))
        }
    
    @vac_routes.add_mcp_tool  
    async def demo_math(a: float, b: float, operation: str = "add") -> float:
        """Perform basic math operations."""
        operations = {
            "add": a + b,
            "subtract": a - b,
            "multiply": a * b,
            "divide": a / b if b != 0 else "Error: Division by zero"
        }
        return operations.get(operation, "Error: Unknown operation")
    
    # Simple VAC simulator that doesn't require any imports
    @vac_routes.add_mcp_tool
    async def demo_vac_chat(user_input: str, vac_name: str = "demo") -> str:
        """
        Simple VAC chat simulator for demo purposes.
        This doesn't require any complex imports.
        """
        responses = {
            "hello": f"Hello from {vac_name} VAC! How can I help you today?",
            "help": f"I'm the {vac_name} VAC. I can answer questions and have conversations.",
            "test": f"Test successful! The {vac_name} VAC is working properly."
        }
        
        # Simple keyword matching
        lower_input = user_input.lower()
        for keyword, response in responses.items():
            if keyword in lower_input:
                return response
        
        # Default response
        return f"The {vac_name} VAC received: '{user_input}'. This is a demo response."
    
    # The /debug/mcp endpoint is now built into VACRoutesFastAPI automatically when MCP is enabled
    
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
                "GET /test - Interactive test page with MCP testing",
                "POST /vac/streaming/{vector_name}",
                "POST /vac/streaming/{vector_name}/sse",
                "POST /vac/{vector_name}",
                "POST /openai/v1/chat/completions",
                "POST /mcp/mcp - MCP server (JSON-RPC endpoint)"
            ],
            "mcp_info": {
                "enabled": True,
                "description": "MCP server is enabled for Claude Code integration",
                "available_tools": ["vac_stream", "vac_query", "list_available_vacs", "get_vac_info"]
            },
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
    <title>VAC FastAPI Demo with MCP</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #007bff; }
        .tab { padding: 10px 20px; cursor: pointer; background: #f0f0f0; border: none; font-size: 16px; }
        .tab.active { background: #007bff; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .container { display: flex; gap: 20px; }
        .section { flex: 1; }
        h1 { color: #333; }
        h2 { color: #555; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
        .input-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 10px; font-size: 14px; box-sizing: border-box; }
        textarea { min-height: 100px; font-family: monospace; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; font-size: 16px; margin-right: 10px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .response { border: 1px solid #ddd; padding: 15px; min-height: 200px; background: #f9f9f9; white-space: pre-wrap; font-family: monospace; overflow-x: auto; }
        .streaming { background: #e8f5e9; }
        .error { background: #ffebee; color: #c62828; }
        .success { background: #e8f5e9; color: #2e7d32; }
        .source { background: #fff3e0; padding: 10px; margin-top: 10px; border-left: 3px solid #ff9800; }
        .tool-item { background: #f5f5f5; padding: 10px; margin: 10px 0; border-left: 3px solid #2196f3; }
        .mcp-section { background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>VAC FastAPI Demo with MCP Server</h1>
    
    <div class="tabs">
        <button class="tab active" onclick="showTab(event, 'streaming')">Streaming Tests</button>
        <button class="tab" onclick="showTab(event, 'mcp')">MCP Server</button>
    </div>
    
    <div id="streaming" class="tab-content active">
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
    </div>
    
    <div id="mcp" class="tab-content">
        <div class="mcp-section">
            <h2>MCP Server Testing</h2>
            <p>The MCP (Model Context Protocol) server enables Claude and other AI assistants to interact with this VAC.</p>
            
            <div class="container">
                <div class="section">
                    <h3>MCP Tools & VACs</h3>
                    <button onclick="listMCPTools()">List Tools</button>
                    <button onclick="listAvailableVACs()">List VACs</button>
                    <button onclick="testDemoTool()">Test Demo Tools</button>
                    <div style="margin-top: 10px;">
                        <label>VAC Name for testing:</label>
                        <input type="text" id="vacTestName" value="demo" style="width: 200px; margin-right: 10px;" />
                        <button onclick="testVACQuery()">Test vac_query</button>
                    </div>
                    <h4>Response:</h4>
                    <div id="mcpToolsList" class="response"></div>
                </div>
                
                <div class="section">
                    <h3>Call MCP Tool</h3>
                    <div class="input-group">
                        <label>Tool Name:</label>
                        <input type="text" id="mcpToolName" value="demo_reverse_text" />
                    </div>
                    <div class="input-group">
                        <label>Arguments (JSON):</label>
                        <textarea id="mcpToolArgs">{
  "text": "Hello from MCP!"
}</textarea>
                    </div>
                    <button onclick="callMCPTool()">Call Tool</button>
                    <h4>Response:</h4>
                    <div id="mcpToolResponse" class="response"></div>
                </div>
            </div>
            
            <div style="margin-top: 30px;">
                <h3>Raw MCP Request</h3>
                <div class="input-group">
                    <label>JSON-RPC Request:</label>
                    <textarea id="mcpRawRequest" style="min-height: 150px;">{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}</textarea>
                </div>
                <button onclick="sendRawMCPRequest()">Send Raw Request</button>
                <h4>Response:</h4>
                <div id="mcpRawResponse" class="response"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Helper function to parse MCP responses (handles both JSON and SSE format)
        // This mirrors the Python sunholo.mcp.parse_sse_response() function
        function parseMCPResponse(text) {
            // Check if it's SSE format
            if (text.startsWith('event:') || text.startsWith('data:')) {
                // Parse SSE format - extract JSON from data: line
                const lines = text.split('\\n');
                const dataLine = lines.find(line => line.startsWith('data:'));
                if (dataLine) {
                    const jsonStr = dataLine.substring(5).trim(); // Remove 'data:' prefix
                    return JSON.parse(jsonStr);
                } else {
                    throw new Error('No data line found in SSE response');
                }
            } else {
                // Try parsing as regular JSON
                return JSON.parse(text);
            }
        }
        
        // Tab switching
        function showTab(event, tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        // MCP Functions
        async function listMCPTools() {
            const responseDiv = document.getElementById('mcpToolsList');
            responseDiv.textContent = 'Loading...';
            responseDiv.className = 'response';
            
            try {
                const response = await fetch('/mcp/mcp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        id: 1,
                        method: 'tools/list'
                    })
                });
                
                console.log('MCP Response status:', response.status);
                console.log('MCP Response headers:', response.headers.get('content-type'));
                
                if (!response.ok) {
                    const text = await response.text();
                    responseDiv.innerHTML = `<strong>MCP endpoint returned ${response.status}</strong><br><br>`;
                    responseDiv.innerHTML += `<strong>Response:</strong><pre>${text}</pre>`;
                    responseDiv.className = 'response error';
                    return;
                }
                
                // Check content type
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('text/html')) {
                    const text = await response.text();
                    responseDiv.innerHTML = `<strong>Error: Got HTML instead of JSON</strong><br><br>`;
                    responseDiv.innerHTML += `<strong>Response:</strong><pre>${text.substring(0, 500)}...</pre>`;
                    responseDiv.className = 'response error';
                    return;
                }
                
                const text = await response.text();
                console.log('MCP Response text:', text);
                
                let data;
                try {
                    data = parseMCPResponse(text);
                } catch (e) {
                    responseDiv.innerHTML = `<strong>Error parsing response:</strong> ${e.message}<br><br>`;
                    responseDiv.innerHTML += `<strong>Raw response:</strong><pre>${text}</pre>`;
                    responseDiv.className = 'response error';
                    return;
                }
                console.log('MCP Response data:', data);
                responseDiv.innerHTML = '<strong>Available MCP Tools:</strong>\\n\\n';
                
                if (data.result && data.result.tools) {
                    data.result.tools.forEach(tool => {
                        responseDiv.innerHTML += `<div class="tool-item">
                            <strong>${tool.name}</strong>
                            <br>Description: ${tool.description || 'No description'}
                            <br>Schema: <pre>${JSON.stringify(tool.inputSchema, null, 2)}</pre>
                        </div>`;
                    });
                } else {
                    responseDiv.textContent = JSON.stringify(data, null, 2);
                }
                responseDiv.className = 'response success';
            } catch (error) {
                console.error('MCP Error:', error);
                responseDiv.textContent = 'Error: ' + error.message + '\\n\\nCheck browser console for details.';
                responseDiv.className = 'response error';
            }
        }
        
        async function testDemoTool() {
            const responseDiv = document.getElementById('mcpToolsList');
            responseDiv.textContent = 'Testing demo tools...';
            responseDiv.className = 'response';
            
            try {
                // Test the simple demo tools
                const response = await fetch('/mcp/mcp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        id: 1,
                        method: 'tools/call',
                        params: {
                            name: 'demo_reverse_text',
                            arguments: {
                                text: 'Hello MCP!'
                            }
                        }
                    })
                });
                
                const text = await response.text();
                const data = parseMCPResponse(text);
                responseDiv.innerHTML = '<strong>Demo Tool Test Results:</strong>\\n\\n';
                responseDiv.innerHTML += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                responseDiv.className = 'response success';
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.className = 'response error';
            }
        }
        
        async function listAvailableVACs() {
            const responseDiv = document.getElementById('mcpToolsList');
            responseDiv.textContent = 'Listing available VACs...';
            responseDiv.className = 'response';
            
            try {
                const response = await fetch('/mcp/mcp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        id: 1,
                        method: 'tools/call',
                        params: {
                            name: 'list_available_vacs',
                            arguments: {}
                        }
                    })
                });
                
                const text = await response.text();
                const data = parseMCPResponse(text);
                responseDiv.innerHTML = '<strong>Available VAC Configurations:</strong>\\n\\n';
                
                if (data.result && data.result.content && data.result.content[0]) {
                    const vacs = JSON.parse(data.result.content[0].text || '[]');
                    if (Array.isArray(vacs)) {
                        responseDiv.innerHTML += '<ul>';
                        vacs.forEach(vac => {
                            responseDiv.innerHTML += `<li><strong>${vac}</strong> <button onclick="document.getElementById('vacTestName').value='${vac}'">Use for testing</button></li>`;
                        });
                        responseDiv.innerHTML += '</ul>';
                    } else {
                        responseDiv.innerHTML += `<pre>${data.result.content[0].text}</pre>`;
                    }
                }
                
                responseDiv.innerHTML += '\\n<strong>Full Response:</strong>\\n';
                responseDiv.innerHTML += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                responseDiv.className = 'response success';
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.className = 'response error';
            }
        }
        
        async function testVACStream() {
            const responseDiv = document.getElementById('mcpToolsList');
            const vacName = document.getElementById('vacTestName').value || 'demo';
            responseDiv.textContent = `Testing vac_stream tool with VAC: ${vacName}...`;
            responseDiv.className = 'response';
            
            try {
                const response = await fetch('/mcp/mcp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        id: 1,
                        method: 'tools/call',
                        params: {
                            name: 'vac_stream',
                            arguments: {
                                vector_name: vacName,
                                user_input: 'Hello from vac_stream test!',
                                chat_history: []
                            }
                        }
                    })
                });
                
                const text = await response.text();
                const data = parseMCPResponse(text);
                responseDiv.innerHTML = '<strong>vac_stream Tool Response:</strong>\\n\\n';
                
                // Extract the actual response from the MCP result
                if (data.result && data.result.content && data.result.content[0]) {
                    responseDiv.innerHTML += `<div class="tool-item">${data.result.content[0].text}</div>`;
                }
                responseDiv.innerHTML += '\\n<strong>Full Response:</strong>\\n';
                responseDiv.innerHTML += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                responseDiv.className = 'response success';
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.className = 'response error';
            }
        }
        
        async function testVACQuery() {
            const responseDiv = document.getElementById('mcpToolsList');
            const vacName = document.getElementById('vacTestName').value || 'demo';
            responseDiv.textContent = `Testing vac_query tool with VAC: ${vacName}...`;
            responseDiv.className = 'response';
            
            try {
                const response = await fetch('/mcp/mcp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        id: 1,
                        method: 'tools/call',
                        params: {
                            name: 'vac_query',
                            arguments: {
                                vector_name: vacName,
                                user_input: 'What can you do?',
                                chat_history: []
                            }
                        }
                    })
                });
                
                const text = await response.text();
                const data = parseMCPResponse(text);
                responseDiv.innerHTML = '<strong>vac_query Tool Response:</strong>\\n\\n';
                
                // Extract the actual response from the MCP result
                if (data.result && data.result.content && data.result.content[0]) {
                    responseDiv.innerHTML += `<div class="tool-item">${data.result.content[0].text}</div>`;
                }
                responseDiv.innerHTML += '\\n<strong>Full Response:</strong>\\n';
                responseDiv.innerHTML += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                responseDiv.className = 'response success';
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.className = 'response error';
            }
        }
        
        async function callMCPTool() {
            const responseDiv = document.getElementById('mcpToolResponse');
            const toolName = document.getElementById('mcpToolName').value;
            const toolArgs = document.getElementById('mcpToolArgs').value;
            
            responseDiv.textContent = 'Calling tool...';
            responseDiv.className = 'response';
            
            try {
                const args = JSON.parse(toolArgs);
                const response = await fetch('/mcp/mcp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        id: 1,
                        method: 'tools/call',
                        params: {
                            name: toolName,
                            arguments: args
                        }
                    })
                });
                
                const text = await response.text();
                const data = parseMCPResponse(text);
                responseDiv.innerHTML = `<strong>Tool Response:</strong>\\n\\n<pre>${JSON.stringify(data, null, 2)}</pre>`;
                responseDiv.className = 'response success';
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.className = 'response error';
            }
        }
        
        async function sendRawMCPRequest() {
            const responseDiv = document.getElementById('mcpRawResponse');
            const requestText = document.getElementById('mcpRawRequest').value;
            
            responseDiv.textContent = 'Sending request...';
            responseDiv.className = 'response';
            
            try {
                const requestData = JSON.parse(requestText);
                const response = await fetch('/mcp/mcp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'
                    },
                    body: JSON.stringify(requestData)
                });
                
                const text = await response.text();
                const data = parseMCPResponse(text);
                responseDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                responseDiv.className = 'response success';
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.className = 'response error';
            }
        }
        
        // Streaming Functions
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
    print("VAC Routes FastAPI Demo Server with MCP")
    print("="*60)
    print(f"Interpreter Type: {'SYNC' if args.sync else 'ASYNC'}")
    print(f"Server URL: http://{args.host}:{args.port}")
    print("\nEndpoints:")
    print(f"  - Interactive Test Page: http://localhost:{args.port}/test")
    print(f"  - API Documentation: http://localhost:{args.port}/docs")
    print(f"  - Server Info: http://localhost:{args.port}/info")
    print(f"  - MCP Server: http://localhost:{args.port}/mcp")
    print("\nTest Commands:")
    print("  # Plain text streaming:")
    print(f'  curl -X POST http://localhost:{args.port}/vac/streaming/demo \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"user_input": "Hello, how are you?"}\'')
    print("\n  # SSE streaming:")
    print(f'  curl -X POST http://localhost:{args.port}/vac/streaming/demo/sse \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"user_input": "Tell me a story"}\'')
    print("\n  # MCP tools list:")
    print(f'  curl -X POST http://localhost:{args.port}/mcp/mcp \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}\'')
    print("\n" + "="*60 + "\n")
    
    # Run the server
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()