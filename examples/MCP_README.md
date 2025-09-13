# MCP Examples

This folder contains example implementations for Sunholo's Model Context Protocol (MCP) integration.

## Available Examples

- **`fastapi_vac_mcp_simple.py`** - Simple FastAPI app with built-in VAC tools and MCP server
- **`fastapi_vac_demo.py`** - Full-featured demo with streaming, MCP tools, and web interface

## Documentation

For complete documentation, installation guides, and advanced usage patterns, see:

📖 **[MCP Integration Guide](../docs/docs/integrations/mcp.md)**

## Quick Setup with create_app_with_mcp

```python
from sunholo.agents.fastapi import VACRoutesFastAPI

# One line to set up everything with MCP server
app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
    title="My VAC App",
    stream_interpreter=my_interpreter
)

# Add custom MCP tools
@vac_routes.add_mcp_tool
async def my_tool(param: str) -> str:
    return f"Result: {param}"
```

## What You Get

- **Built-in VAC tools**: `vac_stream`, `vac_query`, `list_available_vacs`, `get_vac_info`
- **Custom tool registration**: Add your own tools with decorators or programmatically
- **FastAPI integration**: Mount MCP servers in existing FastAPI applications
- **Multiple deployment options**: Local STDIO, remote HTTP, or standalone servers

See the [full documentation](../docs/docs/integrations/mcp.md) for detailed examples and usage patterns.