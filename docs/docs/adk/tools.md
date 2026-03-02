---
title: MCP Tools
sidebar_label: Tools
sidebar_position: 5
---

# MCP Tools

The `sunholo.adk.tools` module provides a decorator pattern for creating MCP-compatible tools that can be used with ADK agents.

## @mcp_tool Decorator

Register functions as MCP tools with automatic schema generation:

```python
from sunholo.adk.tools import mcp_tool

@mcp_tool("search_docs", "Search documentation for relevant information")
async def search_docs(query: str, max_results: int = 10) -> str:
    """Search the documentation.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.
    """
    results = await perform_search(query, limit=max_results)
    return format_results(results)

@mcp_tool("send_email", "Send an email message")
async def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to the specified recipient."""
    await email_service.send(to=to, subject=subject, body=body)
    return f"Email sent to {to}"
```

## Integration with ExtensibleMCPServer

Tools registered with `@mcp_tool` are automatically available when creating an MCP server:

```python
from sunholo.mcp.extensible_mcp_server import create_mcp_server

# All @mcp_tool decorated functions are included
server = create_mcp_server("my-server", include_vac_tools=True)
server.run()
```

## Integration with ADK Agents

MCP tools can be used as ADK agent tools:

```python
from google.adk.agents import Agent
from sunholo.adk.tools import get_registered_tools

# Get all registered MCP tools as ADK-compatible tools
tools = get_registered_tools()

agent = Agent(
    name="assistant",
    model="gemini-2.0-flash",
    tools=tools,
)
```
