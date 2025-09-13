# Model Context Protocol (MCP) Integration

This document explains how to integrate Sunholo VACs (Virtual Agent Computers) with Claude Desktop and Claude Code using the Model Context Protocol (MCP). Sunholo provides a flexible, extensible MCP integration system that allows you to expose VAC functionality and add custom tools for AI applications.

## Overview

Model Context Protocol (MCP) is a standard that allows AI applications to interact with external systems through a set of tools. Sunholo's MCP integration provides:

- **Easy Integration**: Simple setup for Claude Desktop and Claude Code
- **Built-in VAC Tools**: Automatic access to all Sunholo VAC functionality
- **Custom Tools**: Add your own tools using decorators or programmatically
- **Multiple Deployment Options**: Standalone servers, FastAPI integration, or remote servers

## Quick Start

### 1. Basic FastAPI MCP Server

The simplest way to get started is using the `create_app_with_mcp` helper:

```python
from sunholo.agents.fastapi import VACRoutesFastAPI

async def my_interpreter(question, vector_name, chat_history, callback, **kwargs):
    """Your VAC interpreter logic here."""
    return {"answer": f"Response to: {question}", "source_documents": []}

# One line setup with MCP server
app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
    title="My VAC App",
    stream_interpreter=my_interpreter
)

# Add custom tools
@vac_routes.add_mcp_tool
async def my_custom_tool(param: str) -> str:
    return f"Processed: {param}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This gives you immediate access to:
- `vac_stream` - Stream responses from VACs
- `vac_query` - Query VACs (non-streaming)  
- `list_available_vacs` - List all configured VACs
- `get_vac_info` - Get VAC configuration details

### 2. Adding Custom Tools with Decorators

Create your own MCP server with custom tools:

```python
#!/usr/bin/env python3
from sunholo.mcp.extensible_mcp_server import create_mcp_server, mcp_tool

# Global tool registration using decorators
@mcp_tool("get_weather", "Get weather information")
async def get_weather(city: str) -> str:
    """Get weather for a city."""
    # Your weather logic here
    return f"Weather in {city}: Sunny, 22°C"

@mcp_tool("calculate", "Perform calculations") 
async def calculate(expression: str) -> str:
    """Safely evaluate math expressions."""
    try:
        result = eval(expression)  # Use a safer parser in production
        return f"{expression} = {result}"
    except:
        return "Invalid expression"

# Create server with built-in VAC tools + custom tools
server = create_mcp_server("my-custom-server", include_vac_tools=True)

if __name__ == "__main__":
    server.run()
```

Install with:
```bash
fastmcp install claude-desktop my_custom_server.py --with sunholo[anthropic]
```

### 2. FastAPI Integration with Custom Tools

Add MCP tools to your existing FastAPI application:

```python
from sunholo.agents.fastapi import VACRoutesFastAPI
from fastapi import FastAPI

async def my_interpreter(question, vector_name, chat_history, callback, **kwargs):
    """Your VAC interpreter logic."""
    return {"answer": f"Response: {question}", "source_documents": []}

# Method 1: Use the helper method (recommended)
app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
    title="My App",
    stream_interpreter=my_interpreter
)

# Method 2: Manual setup with existing FastAPI app
# app = FastAPI()
# vac_routes = VACRoutesFastAPI(
#     app,
#     stream_interpreter=my_interpreter,
#     enable_mcp_server=True
# )

# Add tools using decorators
@vac_routes.add_mcp_tool
async def get_server_stats() -> dict:
    """Get server statistics."""
    return {"uptime": 3600, "requests": 1234}

@vac_routes.add_mcp_tool("word_count", "Count words in text")
async def count_words(text: str) -> dict:
    """Count words and characters in text."""
    return {
        "words": len(text.split()),
        "characters": len(text)
    }

# Add tools programmatically
async def custom_tool(param: str) -> str:
    return f"Processing: {param}"

vac_routes.add_mcp_tool(custom_tool, "process_data", "Process data")

# Your app is now available at /mcp endpoint for Claude Desktop remote integration
```

## Available MCP Tools

Once connected, Claude Desktop and Claude Code will have access to these built-in tools:

### `vac_stream`
Stream responses from a Sunholo VAC (asynchronous streaming interface).

**Parameters:**
- `vector_name` (string): Name of the VAC to interact with
- `user_input` (string): The user's question or input
- `chat_history` (array, optional): Previous conversation history
- `stream_wait_time` (float, optional): Time to wait between stream chunks (default: 7) 
- `stream_timeout` (float, optional): Maximum time to wait for response (default: 120)

### `vac_query`
Query a Sunholo VAC (non-streaming, same as `vac_stream` but different name for compatibility).

**Parameters:**
- `vector_name` (string): Name of the VAC to interact with
- `user_input` (string): The user's question or input
- `chat_history` (array, optional): Previous conversation history

### `list_available_vacs`
List all available VAC configurations.

**Parameters:** None
**Returns:** Array of available VAC names

### `get_vac_info`
Get detailed information about a specific VAC configuration.

**Parameters:**
- `vector_name` (string): Name of the VAC to get information for

**Returns:** Dictionary with VAC configuration details (name, LLM, model, etc.)

## Installation Options

### Option 1: FastMCP CLI (Recommended)

#### For Claude Desktop:
```bash
# Install FastMCP if not already installed
pip install fastmcp

# Navigate to the examples directory
cd examples/

# Install the Sunholo MCP server
fastmcp install claude-desktop sunholo_mcp_server.py --with sunholo[anthropic]
```

#### For Claude Code:
```bash
# Install the Sunholo MCP server for Claude Code
fastmcp install claude-code sunholo_mcp_server.py --with sunholo[anthropic]
```

### Option 2: Manual Configuration

#### For Claude Desktop:

1. **Install dependencies:**
   ```bash
   pip install sunholo[anthropic] fastmcp
   ```

2. **Configure Claude Desktop:**
   Edit your configuration file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "sunholo-vac": {
         "command": "python",
         "args": ["/path/to/sunholo-py/examples/sunholo_mcp_server.py"],
         "env": {
           "VAC_CONFIG_FOLDER": "/path/to/your/vac/config"
         }
       }
     }
   }
   ```

#### For Claude Code:
Follow the same manual configuration approach as Claude Desktop.

### Option 3: Remote MCP Server

For remote deployments, you can run Sunholo as an HTTP MCP server:

#### 1. Deploy Your FastAPI VAC Server

```python
from sunholo.agents.fastapi import VACRoutesFastAPI

routes = VACRoutesFastAPI(enable_mcp_server=True)

# Deploy to your cloud provider
app = routes.app
```

#### 2. Configure Claude Desktop for Remote MCP

**Note:** Remote MCP servers require Claude Pro, Team, or Enterprise plans.

1. Open Claude Desktop
2. Go to **Settings > Connectors**  
3. Click **"Add custom connector"**
4. Enter your server URL: `https://your-domain.com/mcp`
5. Complete the authentication flow
6. Click **"Add"**

## Advanced Usage

### New Features

#### create_app_with_mcp Helper Method

The `create_app_with_mcp` class method simplifies MCP setup by handling lifespan management automatically:

```python
from sunholo.agents.fastapi import VACRoutesFastAPI

# This method automatically:
# - Creates FastAPI app with proper lifespan
# - Enables MCP server at /mcp endpoint  
# - Registers built-in VAC tools
# - Handles MCP server mounting
app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
    title="My VAC Application",
    stream_interpreter=my_stream_interpreter,
    vac_interpreter=my_vac_interpreter,  # Optional
    app_lifespan=my_lifespan  # Optional custom lifespan
)

# Add custom tools after creation
@vac_routes.add_mcp_tool
async def my_tool(param: str) -> str:
    return f"Result: {param}"
```

#### Debug Endpoint

When using the demo server, a debug endpoint is available at `/debug/mcp` that shows:

```json
{
    "mcp_enabled": true,
    "has_mcp_server": true, 
    "mcp_tools_count": 9,
    "mcp_tools": ["vac_query", "list_available_vacs", "get_vac_info", "demo_reverse_text", "..."],
    "tool_details": [{"name": "vac_query", "description": "Query a Sunholo VAC..."}],
    "pending_tools": 0,
    "message": "MCP server is available at /mcp endpoint with 9 tools"
}
```

#### MCP Server Management Methods

The VACRoutesFastAPI class provides methods for managing MCP tools:

```python
# List registered tools and resources
tools = vac_routes.list_mcp_tools()
resources = vac_routes.list_mcp_resources()

# Get the MCP server instance for advanced usage
mcp_server = vac_routes.get_mcp_server()

# Add resources (data sources)
@vac_routes.add_mcp_resource
async def my_resource(uri: str) -> dict:
    """Provide resource data."""
    return {"data": f"Resource for {uri}"}
```

### Custom Tool Registration

There are multiple ways to register tools:

#### 1. Global Decorator Registration
```python
from sunholo.mcp.extensible_mcp_server import mcp_tool

@mcp_tool("tool_name", "Tool description")
async def my_tool(param: str) -> str:
    return f"Result: {param}"
```

#### 2. Direct Server Registration
```python
server = create_mcp_server("my-server")

@server.add_tool
async def another_tool(data: str) -> str:
    return f"Processed: {data}"
```

#### 3. FastAPI Integration
```python
routes = VACRoutesFastAPI(enable_mcp_server=True)

@routes.add_mcp_tool
async def fastapi_tool(input_data: str) -> str:
    return f"FastAPI processed: {input_data}"
```

#### 4. Programmatic Registration
```python
async def my_function(text: str) -> str:
    return text.upper()

# Add to server
server.add_tool(my_function, "uppercase_text", "Convert text to uppercase")

# Or add to FastAPI routes
routes.add_mcp_tool(my_function, "uppercase_text", "Convert text to uppercase")
```

### Resource Registration

MCP also supports resources (data sources):

```python
from sunholo.mcp.extensible_mcp_server import mcp_resource

@mcp_resource("system_info", "Get system information")
async def get_system_info(resource_uri: str) -> dict:
    """Get system information resource."""
    return {
        "system": "Linux",
        "python_version": "3.11",
        "resource_uri": resource_uri
    }
```

### Environment Configuration

Configure the MCP server with environment variables:

```bash
# Default VAC to use
export DEFAULT_VAC_NAME="my-chatbot"

# Path to VAC configuration files  
export VAC_CONFIG_FOLDER="/path/to/configs"

# Logging level
export LOG_LEVEL="INFO"
```

Or set in Claude Desktop configuration:
```json
{
  "mcpServers": {
    "my-sunholo-server": {
      "command": "python",
      "args": ["/path/to/my_server.py"],
      "env": {
        "DEFAULT_VAC_NAME": "my-chatbot",
        "VAC_CONFIG_FOLDER": "/Users/me/vac-configs"
      }
    }
  }
}
```

## Deployment Options

### Option 1: Local Claude Desktop Integration
```bash
# Install directly with FastMCP
fastmcp install claude-desktop my_server.py --with sunholo[anthropic]

# Or manual configuration in claude_desktop_config.json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/path/to/my_server.py"]
    }
  }
}
```

### Option 2: Claude Code Integration  
```bash
fastmcp install claude-code my_server.py --with sunholo[anthropic]
```

### Option 3: Remote FastAPI Server
```python
# Deploy your FastAPI app with MCP enabled
routes = VACRoutesFastAPI(enable_mcp_server=True)
app = routes.app

# Deploy to cloud provider, then configure Claude Desktop:
# Settings > Connectors > Add custom connector
# URL: https://your-domain.com/mcp
```

## Testing the Integration

### 1. Test FastAPI MCP Server

Test the MCP server directly:

```bash
# Run the simple example
python examples/fastapi_vac_mcp_simple.py

# In another terminal, test the MCP endpoint
curl -X POST http://localhost:8000/mcp/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Test the debug endpoint (if using fastapi_vac_demo.py)
curl http://localhost:8000/debug/mcp
```

The server provides both HTTP endpoints and MCP tools.

### 2. Test with Claude Desktop/Code

Once configured using FastMCP CLI or manual configuration:

**In Claude Desktop:**
1. Start a new conversation
2. Type: "Use the vac_stream tool to ask 'What is machine learning?' to the 'demo' VAC"
3. Claude will automatically use the MCP tool

**In Claude Code:**
1. The tools will be available automatically
2. Use them in conversation: "List available VACs and then query the demo VAC about Python programming"

### 3. Test Available Tools

Try these example prompts in Claude Desktop or Claude Code:

```
- "List all available VACs using the list_available_vacs tool"
- "Get information about the demo VAC using get_vac_info"  
- "Use vac_stream to ask the demo VAC: 'Explain quantum computing'"
- "Query the demo VAC about 'best practices for API design'"
```

### 4. Verify Installation

Check that the MCP server is properly installed:

```bash
# For Claude Desktop
fastmcp list claude-desktop

# For Claude Code  
fastmcp list claude-code
```

## Example Use Cases

### Example 1: Business Logic Integration
```python
@mcp_tool("search_customers", "Search customer database")
async def search_customers(query: str) -> list:
    """Search customers by name or email."""
    # Your database logic here
    return [
        {"name": "John Doe", "email": "john@example.com"},
        {"name": "Jane Smith", "email": "jane@example.com"}
    ]

@mcp_tool("get_order_status", "Get order status by ID") 
async def get_order_status(order_id: str) -> dict:
    """Get status of an order."""
    # Your order system logic here
    return {
        "order_id": order_id,
        "status": "shipped",
        "tracking": "1234567890"
    }
```

### Example 2: External API Integration
```python
import httpx

@mcp_tool("translate_text", "Translate text between languages")
async def translate_text(text: str, target_lang: str = "es") -> str:
    """Translate text to target language."""
    # Integration with translation service
    async with httpx.AsyncClient() as client:
        # Your translation API call here
        return f"Translated '{text}' to {target_lang}: [translation result]"
```

### Example 3: File System Operations
```python
from pathlib import Path

@mcp_tool("list_project_files", "List files in project directory")
async def list_project_files(directory: str = ".") -> list:
    """List files in a project directory."""
    try:
        path = Path(directory)
        return [f.name for f in path.iterdir() if f.is_file()]
    except Exception as e:
        return [f"Error: {str(e)}"]

@mcp_tool("read_config_file", "Read application configuration")
async def read_config_file(config_name: str) -> dict:
    """Read configuration file."""
    config_path = Path(f"configs/{config_name}.json")
    if config_path.exists():
        import json
        return json.loads(config_path.read_text())
    return {"error": "Config file not found"}
```

## Best Practices

### 1. Tool Design
- **Clear Descriptions**: Provide detailed docstrings and descriptions
- **Type Hints**: Use proper type hints for parameters and return values
- **Error Handling**: Always handle exceptions gracefully
- **Parameter Validation**: Validate inputs before processing

### 2. Security Considerations
- **Input Sanitization**: Always validate and sanitize user inputs
- **Resource Limits**: Implement timeouts and resource limits
- **Authentication**: Use proper authentication for remote servers
- **Sensitive Data**: Never expose secrets or sensitive information

### 3. Performance
- **Async Operations**: Use async/await for I/O operations
- **Caching**: Implement caching for expensive operations
- **Resource Management**: Properly manage database connections and API clients
- **Error Recovery**: Implement retry logic for external services

### 4. Development Workflow
```python
# Development server with auto-reload
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true", help="Development mode")
    args = parser.parse_args()
    
    if args.dev:
        print("Development mode - tools may have debug output")
    
    server.run()
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install sunholo[anthropic] fastmcp
   ```

2. **FastMCP Not Found**: Install FastMCP separately if needed
   ```bash  
   pip install fastmcp>=2.12.0
   ```

3. **VAC Tools Not Working**: Check environment variables and VAC configuration
   ```bash
   export DEFAULT_VAC_NAME="demo"
   export VAC_CONFIG_FOLDER="/path/to/configs"
   ```

4. **Claude Desktop Connection Issues**: 
   - Check MCP server is running
   - Verify configuration file syntax
   - Check server logs for errors

5. **Tools Not Appearing**: 
   - Ensure tools are properly registered
   - Check for import errors
   - Verify FastMCP server startup

### MCP Server Not Available
- Check that `enable_mcp_server=True` is set
- Verify FastMCP is installed: `pip install fastmcp>=2.12.0`
- Check server logs for mounting errors

### Connection Issues
- Ensure the correct port and URL in Claude Code config
- Verify the server is running and accessible
- Check firewall settings if running on different machines

### Tool Execution Errors
- Verify `vector_name` exists in your VAC configuration
- Check interpreter functions are properly configured
- Review server logs for detailed error messages

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# List registered tools
server = create_mcp_server("debug-server")
print(f"Registered tools: {server.list_registered_tools()}")
print(f"Registered resources: {server.list_registered_resources()}")
```

## Multiple VACs

You can run multiple VAC servers on different ports and configure Claude to access multiple MCP servers:

```json
{
  "mcpServers": {
    "vac-chatbot": {
      "transport": "http",
      "url": "http://localhost:8000/mcp"
    },
    "vac-analysis": {
      "transport": "http", 
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

## Production Deployment

For production use:

1. Use HTTPS endpoints
2. Configure proper authentication
3. Set appropriate timeouts
4. Monitor MCP tool usage
5. Consider rate limiting

## Security Considerations for Remote MCP

- Only connect to trusted servers
- Review requested permissions carefully
- Monitor for unexpected behavior
- Use HTTPS for production deployments
- Implement proper authentication and rate limiting

## Migration from Old MCP Integration

If you're upgrading from the old MCP integration:

### Before (Old System)
```python
from sunholo.mcp.vac_mcp_server_fastmcp import VACMCPServer

server = VACMCPServer(stream_interpreter=my_func)
```

### After (New System) 
```python
from sunholo.mcp.extensible_mcp_server import create_mcp_server

# Built-in VAC tools are included automatically
server = create_mcp_server("my-server", include_vac_tools=True)

# Add custom tools easily
@server.add_tool
async def my_custom_tool(param: str) -> str:
    return f"Result: {param}"
```

The new system is backward compatible, but we recommend migrating to the extensible system for better flexibility and easier tool management.

## Support

For questions or issues:

1. Check the examples in `/examples/`
2. Review this integration guide 
3. File issues at: https://github.com/sunholo-data/sunholo-py/issues

The extensible MCP system makes it easy to create powerful Claude Desktop and Claude Code integrations with both built-in VAC functionality and your own custom tools!