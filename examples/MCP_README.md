# MCP Examples

This folder contains example implementations for Sunholo's Model Context Protocol (MCP) integration.

## Quick Start Files

- **`sunholo_mcp_server.py`** - Basic MCP server with built-in VAC tools
- **`extensible_mcp_demo.py`** - Advanced demo with custom tools and FastAPI integration
- **`mcp_fastmcp_example.py`** - Simple FastMCP integration example
- **`mcp_server_example.py`** - Legacy MCP server example

## Documentation

For complete documentation, installation guides, and advanced usage patterns, see:

📖 **[MCP Integration Guide](../docs/docs/integrations/mcp.md)**

## Quick Installation

```bash
# For Claude Desktop
fastmcp install claude-desktop sunholo_mcp_server.py --with sunholo[anthropic]

# For Claude Code  
fastmcp install claude-code sunholo_mcp_server.py --with sunholo[anthropic]
```

## What You Get

- **Built-in VAC tools**: `vac_stream`, `vac_query`, `list_available_vacs`, `get_vac_info`
- **Custom tool registration**: Add your own tools with decorators or programmatically
- **FastAPI integration**: Mount MCP servers in existing FastAPI applications
- **Multiple deployment options**: Local STDIO, remote HTTP, or standalone servers

See the [full documentation](../docs/docs/integrations/mcp.md) for detailed examples and usage patterns.