# MCP Server with FastMCP

This guide explains the new FastMCP-based implementation of the Sunholo VAC MCP server, which provides a simpler and more Pythonic way to expose VAC functionality via the Model Context Protocol.

## What's Changed

The Sunholo MCP implementation now uses **FastMCP**, which provides:

- **70% less boilerplate code** compared to the standard MCP SDK
- **Automatic schema generation** from Python type hints
- **Decorator-based tool registration** for cleaner code
- **Built-in transport handling** for both stdio and HTTP
- **Better async support** and error handling

## Key Benefits

### Before (Standard MCP SDK)
```python
# ~266 lines of complex setup code
class VACMCPServer:
    def _setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            tools = [
                Tool(
                    name="vac_stream",
                    description="Stream responses...",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            # 30+ lines of manual schema definition
                        }
                    }
                )
            ]
```

### After (FastMCP)
```python
# ~150 lines of clean, readable code
from fastmcp import FastMCP

mcp = FastMCP("sunholo-vac-server")

@mcp.tool
async def vac_stream(
    vector_name: str,
    user_input: str,
    chat_history: List[Dict[str, str]] = None
) -> str:
    """Stream responses from a Sunholo VAC."""
    # Direct implementation - schema auto-generated from type hints
```

## Usage

The FastMCP implementation is now the default. When you enable MCP server in your VAC:

```python
from sunholo.agents.fastapi import VACRoutesFastAPI

vac_routes = VACRoutesFastAPI(
    app,
    stream_interpreter=your_interpreter,
    enable_mcp_server=True  # Uses FastMCP automatically
)
```

## Available Tools

The FastMCP implementation exposes the same tools with improved definitions:

### vac_stream
Streams responses from a Sunholo VAC with automatic type validation.

```python
@mcp.tool
async def vac_stream(
    vector_name: str,           # Required: VAC name
    user_input: str,            # Required: User's question
    chat_history: List = None,  # Optional: Conversation history
    stream_wait_time: float = 7,    # Optional: Chunk wait time
    stream_timeout: float = 120     # Optional: Total timeout
) -> str:
```

### vac_query
Non-streaming VAC queries (when vac_interpreter is provided).

```python
@mcp.tool
async def vac_query(
    vector_name: str,
    user_input: str,
    chat_history: List = None
) -> str:
```

## CLI Commands

The CLI now uses FastMCP for both server and bridge modes:

### MCP Server (stdio mode for Claude Desktop)
```bash
sunholo mcp server
```

### HTTP Server Mode
```bash
sunholo mcp bridge http://127.0.0.1:8000/mcp
```

FastMCP handles the transport layer automatically, eliminating the need for a separate stdio-to-HTTP bridge in many cases.

## Claude Desktop Configuration

The configuration remains the same, but the underlying implementation is now more robust:

```json
{
  "mcpServers": {
    "sunholo-vac": {
      "command": "sunholo",
      "args": ["mcp", "server"]
    }
  }
}
```

## Testing Your MCP Server

### Quick Test
```bash
# Run the example
python examples/mcp_fastmcp_example.py

# In another terminal, test the MCP endpoint
curl http://localhost:8000/mcp
```

### Test Tool Execution
```python
from fastmcp import FastMCP

# The server automatically validates inputs
# Invalid types or missing required fields will raise clear errors
```

## Migration Notes

If you have existing code using the old MCP implementation:

1. **No code changes required** - The interface remains the same
2. **Better error messages** - FastMCP provides clearer validation errors
3. **Improved performance** - Less overhead from manual schema handling
4. **Simplified debugging** - Cleaner stack traces and error messages

## Advanced Features

### Custom Transport Configuration
```python
# FastMCP supports multiple transports
mcp.run(transport="http", port=8000)  # HTTP mode
mcp.run(transport="stdio")            # stdio mode (default)
```

### Type-Safe Tool Definitions
```python
from typing import Optional, List, Dict

@mcp.tool
async def advanced_vac_tool(
    required_param: str,
    optional_param: Optional[int] = None,
    list_param: List[str] = None,
    dict_param: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    FastMCP automatically generates the correct schema
    from these type hints - no manual definition needed!
    """
    return {"result": "processed"}
```

## Troubleshooting

### ImportError for FastMCP
Ensure FastMCP is installed:
```bash
pip install fastmcp>=2.12.0
```

### Tool Not Appearing in Claude
FastMCP tools are registered at module import time. Ensure your interpreter functions are defined before creating the VACMCPServer instance.

### Type Validation Errors
FastMCP validates all inputs against the type hints. Ensure your tool functions have proper type annotations.

## Performance Improvements

The FastMCP implementation provides:
- **Faster startup** - Less initialization overhead
- **Lower memory usage** - No redundant schema storage
- **Better async performance** - Optimized for async/await patterns
- **Reduced latency** - Direct tool invocation without intermediate layers

## See Also

- [FastMCP Documentation](https://gofastmcp.com)
- [Original MCP Server Guide](mcp_server.md)
- [Creating a VAC](creating_a_vac.md)
- [Model Context Protocol](https://modelcontextprotocol.io)