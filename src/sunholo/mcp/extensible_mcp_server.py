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
Extensible MCP Server for Sunholo applications.
Allows easy integration with Claude Desktop/Code and custom tool registration.
"""

from typing import Any, Callable, Dict, List, Optional, Union
import asyncio
import inspect
from functools import wraps

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FastMCP = None
    FASTMCP_AVAILABLE = False

from ..custom_logging import log


class MCPToolRegistry:
    """Registry for MCP tools that can be shared across server instances."""
    
    def __init__(self):
        self.tools = {}
        self.resources = {}
        
    def register_tool(self, name: str, func: Callable, description: str = None):
        """Register a tool function."""
        self.tools[name] = {
            'func': func,
            'description': description or func.__doc__,
            'signature': inspect.signature(func)
        }
        
    def register_resource(self, name: str, func: Callable, description: str = None):
        """Register a resource function."""
        self.resources[name] = {
            'func': func,
            'description': description or func.__doc__,
            'signature': inspect.signature(func)
        }
        
    def get_tool(self, name: str):
        """Get a registered tool."""
        return self.tools.get(name)
        
    def get_resource(self, name: str):
        """Get a registered resource."""
        return self.resources.get(name)
        
    def list_tools(self):
        """List all registered tools."""
        return list(self.tools.keys())
        
    def list_resources(self):
        """List all registered resources."""
        return list(self.resources.keys())


# Global registry instance
_global_registry = MCPToolRegistry()


def mcp_tool(name: str = None, description: str = None):
    """
    Decorator to register a function as an MCP tool.
    
    Args:
        name: Optional custom name for the tool
        description: Optional description (uses docstring if not provided)
    
    Example:
        @mcp_tool("my_custom_tool", "Does something useful")
        async def my_tool(param1: str, param2: int = 5) -> str:
            return f"Result: {param1} * {param2}"
    """
    def decorator(func):
        tool_name = name or func.__name__
        _global_registry.register_tool(tool_name, func, description)
        return func
    return decorator


def mcp_resource(name: str = None, description: str = None):
    """
    Decorator to register a function as an MCP resource.
    
    Args:
        name: Optional custom name for the resource
        description: Optional description (uses docstring if not provided)
    """
    def decorator(func):
        resource_name = name or func.__name__
        _global_registry.register_resource(resource_name, func, description)
        return func
    return decorator


class ExtensibleMCPServer:
    """
    Extensible MCP Server that supports custom tool registration.
    Can be used both as a standalone server and integrated into FastAPI apps.
    """
    
    def __init__(
        self, 
        server_name: str = "extensible-mcp-server",
        registry: MCPToolRegistry = None,
        include_vac_tools: bool = True
    ):
        """
        Initialize the extensible MCP server.
        
        Args:
            server_name: Name for the MCP server
            registry: Custom tool registry (uses global if None)
            include_vac_tools: Whether to include built-in VAC tools
        """
        if not FASTMCP_AVAILABLE:
            raise ImportError(
                "fastmcp is required for MCP server functionality. "
                "Install it with: pip install fastmcp>=2.12.0"
            )
            
        self.server_name = server_name
        self.registry = registry or _global_registry
        self.include_vac_tools = include_vac_tools
        
        # Initialize FastMCP server
        self.server = FastMCP(server_name)
        
        # Register tools and resources
        self._register_tools()
        self._register_resources()
        
        # Register built-in VAC tools if requested
        if include_vac_tools:
            self._register_vac_tools()
    
    def _register_tools(self):
        """Register all tools from the registry with FastMCP."""
        for tool_name, tool_info in self.registry.tools.items():
            func = tool_info['func']
            
            # Register with FastMCP using the @self.server.tool decorator
            self.server.tool(func)
            
            log.debug(f"Registered MCP tool: {tool_name}")
    
    def _register_resources(self):
        """Register all resources from the registry with FastMCP."""
        for resource_name, resource_info in self.registry.resources.items():
            func = resource_info['func']
            
            # Register with FastMCP (resources are handled differently)
            # For now, we'll treat resources as tools since FastMCP doesn't have separate resource registration
            self.server.tool(func)
            
            log.debug(f"Registered MCP resource: {resource_name}")
    
    def _register_vac_tools(self):
        """Register built-in VAC tools."""
        from .vac_tools import register_vac_tools
        register_vac_tools(self.server, self.registry)
    
    def add_tool(self, func: Callable, name: str = None, description: str = None):
        """
        Add a tool function directly to the server.
        
        Args:
            func: The tool function
            name: Optional custom name
            description: Optional description
        """
        tool_name = name or func.__name__
        self.registry.register_tool(tool_name, func, description)
        self.server.tool(func)
        log.info(f"Added MCP tool: {tool_name}")
    
    def add_resource(self, func: Callable, name: str = None, description: str = None):
        """
        Add a resource function directly to the server.
        
        Args:
            func: The resource function
            name: Optional custom name  
            description: Optional description
        """
        resource_name = name or func.__name__
        self.registry.register_resource(resource_name, func, description)
        self.server.tool(func)  # FastMCP treats resources as tools
        log.info(f"Added MCP resource: {resource_name}")
    
    def get_server(self) -> FastMCP:
        """Get the underlying FastMCP server instance."""
        return self.server
    
    def get_http_app(self):
        """Get the HTTP app for mounting in FastAPI."""
        return self.server.get_app()
    
    def run(self, transport: str = "stdio", **kwargs):
        """
        Run the MCP server.
        
        Args:
            transport: Transport type ("stdio" or "http")
            **kwargs: Additional arguments for the transport
        """
        self.server.run(transport=transport, **kwargs)
    
    async def run_async(self, transport: str = "stdio", **kwargs):
        """
        Run the MCP server asynchronously.
        
        Args:
            transport: Transport type ("stdio" or "http")
            **kwargs: Additional arguments for the transport
        """
        await self.server.run_async(transport=transport, **kwargs)
    
    def list_registered_tools(self) -> List[str]:
        """List all registered tools."""
        return self.registry.list_tools()
    
    def list_registered_resources(self) -> List[str]:
        """List all registered resources.""" 
        return self.registry.list_resources()


def get_global_registry() -> MCPToolRegistry:
    """Get the global MCP tool registry."""
    return _global_registry


def create_mcp_server(
    server_name: str = "sunholo-mcp-server",
    include_vac_tools: bool = True,
    custom_registry: MCPToolRegistry = None
) -> ExtensibleMCPServer:
    """
    Create a new extensible MCP server instance.
    
    Args:
        server_name: Name for the MCP server
        include_vac_tools: Whether to include built-in VAC tools
        custom_registry: Optional custom tool registry
    
    Returns:
        Configured ExtensibleMCPServer instance
    """
    return ExtensibleMCPServer(
        server_name=server_name,
        registry=custom_registry,
        include_vac_tools=include_vac_tools
    )