# MCP Integration with VACRoutes

This document explains how to use the Model Context Protocol (MCP) capabilities integrated into VACRoutes for building AI applications with external tool access.

## Overview

The VACRoutes class now supports MCP (Model Context Protocol) integration, allowing your AI agents to:
- Connect to external MCP servers
- List and call tools provided by MCP servers
- Access resources from MCP servers
- Use multiple MCP servers simultaneously

## Quick Start

### 1. Basic Setup

```python
from flask import Flask
from sunholo.agents.flask.vac_routes import VACRoutes

app = Flask(__name__)

def stream_interpreter(question, vector_name, chat_history, **kwargs):
    # Your AI logic here
    return {"answer": f"Response to: {question}"}

# Configure MCP servers
mcp_servers = [
    {
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    },
    {
        "name": "brave_search",
        "command": "npx", 
        "args": ["-y", "@modelcontextprotocol/server-brave-search"]
    }
]

# Initialize VACRoutes with MCP support
vac_routes = VACRoutes(
    app=app,
    stream_interpreter=stream_interpreter,
    mcp_servers=mcp_servers
)

if __name__ == "__main__":
    app.run(debug=True)
```

### 2. MCP Server Configuration

Each MCP server configuration requires:
- **name**: Unique identifier for the server
- **command**: Executable command to start the server
- **args**: Command line arguments (optional)

```python
mcp_servers = [
    {
        "name": "server_name",
        "command": "command_to_run", 
        "args": ["--arg1", "value1", "--arg2", "value2"]  # Optional
    }
]
```

## Available MCP Endpoints

When MCP servers are configured, VACRoutes automatically registers these endpoints:

### List Tools
```http
GET /mcp/tools
GET /mcp/tools/<server_name>
```

**Response:**
```json
{
  "tools": [
    {
      "name": "read_file",
      "description": "Read contents of a file",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": {"type": "string"}
        }
      },
      "server": "filesystem"
    }
  ]
}
```

### Call Tool
```http
POST /mcp/call
```

**Request:**
```json
{
  "server": "filesystem",
  "tool": "read_file",
  "arguments": {
    "path": "/path/to/file.txt"
  }
}
```

**Response:**
```json
{
  "result": "File contents here..."
}
```

### List Resources
```http
GET /mcp/resources
GET /mcp/resources?server=<server_name>
```

**Response:**
```json
{
  "resources": [
    {
      "uri": "file:///path/to/resource",
      "name": "Resource Name",
      "description": "Resource description",
      "mimeType": "text/plain",
      "server": "filesystem"
    }
  ]
}
```

### Read Resource
```http
POST /mcp/resources/read
```

**Request:**
```json
{
  "server": "filesystem",
  "uri": "file:///path/to/resource"
}
```

**Response:**
```json
{
  "contents": [
    {"text": "Resource content here..."}
  ]
}
```

## Using MCP in Your AI Agent

### 1. In Stream Interpreter

```python
import requests
import json

def stream_interpreter(question, vector_name, chat_history, **kwargs):
    # Check if the question requires external tools
    if "read file" in question.lower():
        # Call MCP tool
        response = requests.post('http://localhost:5000/mcp/call', json={
            "server": "filesystem",
            "tool": "read_file", 
            "arguments": {"path": "/path/to/file.txt"}
        })
        
        if response.status_code == 200:
            file_content = response.json()["result"]
            return {"answer": f"File content: {file_content}"}
    
    # Normal AI processing
    return {"answer": f"Response to: {question}"}
```

### 2. With LangChain Integration

```python
from langchain.tools import Tool
import requests

def create_mcp_tool(server_name, tool_name, description):
    def mcp_tool_func(arguments_json):
        try:
            arguments = json.loads(arguments_json)
            response = requests.post('http://localhost:5000/mcp/call', json={
                "server": server_name,
                "tool": tool_name,
                "arguments": arguments
            })
            return response.json().get("result", "Error calling tool")
        except Exception as e:
            return f"Error: {str(e)}"
    
    return Tool(
        name=f"{server_name}_{tool_name}",
        description=description,
        func=mcp_tool_func
    )

# Get available tools and create LangChain tools
tools_response = requests.get('http://localhost:5000/mcp/tools')
langchain_tools = []

for tool in tools_response.json()["tools"]:
    langchain_tool = create_mcp_tool(
        server_name=tool["server"],
        tool_name=tool["name"],
        description=tool["description"]
    )
    langchain_tools.append(langchain_tool)
```

## Popular MCP Servers

### Filesystem Server
```python
{
    "name": "filesystem",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
}
```

### Brave Search Server
```python
{
    "name": "brave_search", 
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"]
}
```

### Git Server
```python
{
    "name": "git",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-git", "--repository", "/path/to/repo"]
}
```

### SQLite Server
```python
{
    "name": "sqlite",
    "command": "npx", 
    "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/path/to/database.db"]
}
```

## Environment Variables

Some MCP servers require environment variables:

```python
import os

# For Brave Search
os.environ["BRAVE_API_KEY"] = "your-brave-api-key"

# For other services
os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = "your-token"
```

## Error Handling

The MCP integration includes automatic error handling:

```python
# Tool call errors return HTTP 500 with error details
{
  "error": "Tool execution failed: reason"
}

# Server connection errors are logged but don't crash the application
```

## Advanced Configuration

### Async Streaming with MCP

```python
# Enable async streaming for better performance
vac_routes = VACRoutes(
    app=app,
    stream_interpreter=async_stream_interpreter,
    mcp_servers=mcp_servers,
    async_stream=True  # Enable async streaming
)
```

### Custom MCP Server

You can also connect to custom MCP servers:

```python
{
    "name": "custom_server",
    "command": "python",
    "args": ["/path/to/your/mcp_server.py"]
}
```

## Troubleshooting

### Common Issues

1. **Server not found**: Ensure the MCP server command is in your PATH
2. **Connection failures**: Check server logs and ensure proper permissions
3. **Tool not available**: Verify the server is running and tools are properly exposed

### Debug Mode

Enable debug logging to troubleshoot MCP issues:

```python
import logging
logging.getLogger('sunholo.mcp').setLevel(logging.DEBUG)
```

### Testing MCP Integration

Use the provided test endpoints to verify MCP functionality:

```bash
# List available tools
curl http://localhost:5000/mcp/tools

# Test tool call
curl -X POST http://localhost:5000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"server": "filesystem", "tool": "list_directory", "arguments": {"path": "/"}}'
```

## Best Practices

1. **Server Management**: Keep MCP servers lightweight and focused
2. **Error Handling**: Always handle MCP tool failures gracefully
3. **Security**: Only expose necessary directories/resources to MCP servers
4. **Performance**: Use async streaming for better responsiveness
5. **Monitoring**: Log MCP tool usage for debugging and optimization

## Next Steps

- Explore the [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
- Build custom MCP servers for your specific use cases
- Integrate MCP tools with your existing AI workflows
- Monitor and optimize MCP tool performance