#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
FastMCP-based MCP Server wrapper for VAC functionality.
This module exposes VAC streaming capabilities as MCP tools using FastMCP.
Now uses the extensible MCP server system for better customization.
"""

from typing import Any, Callable, Dict, List, Optional

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FastMCP = None
    FASTMCP_AVAILABLE = False

from ..custom_logging import log
from .extensible_mcp_server import ExtensibleMCPServer, MCPToolRegistry


class VACMCPServer:
    """
    FastMCP Server that exposes VAC functionality as tools.
    Now built on top of ExtensibleMCPServer for better customization.
    """
    
    def __init__(
        self, 
        server_name: str = "sunholo-vac-server",
        include_vac_tools: bool = True,
        custom_registry: MCPToolRegistry = None
    ):
        """
        Initialize the VAC MCP Server using FastMCP.
        
        Args:
            server_name: Name for the MCP server
            include_vac_tools: Whether to include built-in VAC tools
            custom_registry: Optional custom tool registry
        """
        if not FASTMCP_AVAILABLE:
            raise ImportError(
                "fastmcp is required for MCP server functionality. "
                "Install it with: pip install fastmcp>=2.12.0"
            )
        
        # Use the extensible MCP server
        self.extensible_server = ExtensibleMCPServer(
            server_name=server_name,
            registry=custom_registry,
            include_vac_tools=include_vac_tools
        )
        
        # Expose server for compatibility
        self.server = self.extensible_server.server
    
    def get_server(self) -> FastMCP:
        """Get the underlying FastMCP server instance."""
        return self.server
    
    def get_http_app(self):
        """Get the HTTP app for mounting in FastAPI."""
        # Use path="" when mounting at a subpath to avoid double nesting
        # Mount at /mcp/mcp to get /mcp/mcp endpoint without intercepting other routes
        return self.server.http_app(path="")
    
    def add_tool(self, func: Callable, name: str = None, description: str = None):
        """
        Add a custom tool function to the MCP server.
        
        Args:
            func: The tool function
            name: Optional custom name
            description: Optional description
        """
        self.extensible_server.add_tool(func, name, description)
    
    def add_resource(self, func: Callable, name: str = None, description: str = None):
        """
        Add a custom resource function to the MCP server.
        
        Args:
            func: The resource function
            name: Optional custom name  
            description: Optional description
        """
        self.extensible_server.add_resource(func, name, description)
    
    def get_registry(self) -> MCPToolRegistry:
        """Get the tool registry for advanced customization."""
        return self.extensible_server.registry
    
    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return self.extensible_server.list_registered_tools()
    
    def list_resources(self) -> List[str]:
        """List all registered resources."""
        return self.extensible_server.list_registered_resources()
    
    def run(self, transport: str = "stdio", **kwargs):
        """
        Run the MCP server.
        
        Args:
            transport: Transport type ("stdio" or "http")
            **kwargs: Additional arguments for the transport
        """
        self.extensible_server.run(transport=transport, **kwargs)
    
    async def run_async(self, transport: str = "stdio", **kwargs):
        """
        Run the MCP server asynchronously.
        
        Args:
            transport: Transport type ("stdio" or "http")
            **kwargs: Additional arguments for the transport
        """
        await self.extensible_server.run_async(transport=transport, **kwargs)