#!/usr/bin/env python3
"""
Standalone Sunholo MCP Server for Claude Desktop and Claude Code integration.

This script creates a FastMCP server that exposes Sunholo VAC functionality
as MCP tools for use with Claude Desktop and Claude Code.

Usage:
    # Install for Claude Desktop
    fastmcp install claude-desktop sunholo_mcp_server.py --with sunholo[anthropic]
    
    # Install for Claude Code  
    fastmcp install claude-code sunholo_mcp_server.py --with sunholo[anthropic]
    
    # Manual configuration in claude_desktop_config.json:
    {
      "mcpServers": {
        "sunholo-vac": {
          "command": "python",
          "args": ["sunholo_mcp_server.py"],
          "env": {
            "VAC_CONFIG_FOLDER": "/path/to/your/config"
          }
        }
      }
    }
"""

import asyncio
import os
import sys
from typing import Dict, List, Optional, Any

# Add the sunholo package to path if running from examples directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from sunholo.mcp.extensible_mcp_server import create_mcp_server
    from sunholo.custom_logging import log
except ImportError as e:
    print(f"Error importing Sunholo modules: {e}")
    print("Make sure sunholo is installed: pip install sunholo[anthropic]")
    sys.exit(1)

# Initialize extensible MCP server with built-in VAC tools
mcp_server = create_mcp_server(
    server_name="sunholo-vac",
    include_vac_tools=True
)

# The VAC tools are now automatically included via the extensible MCP server

# Optionally add custom tools specific to this server instance
@mcp_server.get_server().tool
async def server_status() -> Dict[str, Any]:
    """Get the status of this MCP server instance."""
    return {
        "server_name": "sunholo-vac",
        "status": "running",
        "tools_available": len(mcp_server.list_registered_tools()),
        "resources_available": len(mcp_server.list_registered_resources()),
        "description": "Sunholo VAC MCP Server with built-in tools"
    }

if __name__ == "__main__":
    # Run the MCP server
    mcp_server.run()