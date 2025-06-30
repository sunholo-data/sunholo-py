"""
Proper MCP integration for VACRoutes using the official MCP Python SDK.
This shows how to integrate MCP servers with your Flask/VACRoutes application.
"""

from typing import Dict, Any, List, Optional
import asyncio

# MCP SDK imports - try different import paths
try:
    from mcp.client.stdio import StdioClientTransport
    from mcp.client.session import ClientSession
except ImportError:
    try:
        # Alternative import paths
        from mcp.client import StdioClientTransport, ClientSession
    except ImportError:
        try:
            # Another alternative
            from mcp import StdioClientTransport, ClientSession
        except ImportError:
            StdioClientTransport = None
            ClientSession = None

try:
    from mcp.types import Tool, Resource, TextContent, CallToolResult
except ImportError:
    try:
        from mcp import Tool, Resource, TextContent, CallToolResult
    except ImportError:
        Tool = None
        Resource = None
        TextContent = None
        CallToolResult = None


class MCPClientManager:
    """Manages MCP client connections to various MCP servers."""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.server_configs: Dict[str, Dict[str, Any]] = {}
        
    async def connect_to_server(self, server_name: str, command: str, args: List[str] = None) -> ClientSession:
        """Connect to an MCP server via stdio."""
        if server_name in self.sessions:
            return self.sessions[server_name]
        
        if not StdioClientTransport or not ClientSession:
            raise ImportError("MCP client dependencies not available")
        
        # Create transport and session
        transport = StdioClientTransport(
            command=command,
            args=args or []
        )
        session = ClientSession(transport)
        await session.initialize()
        
        self.sessions[server_name] = session
        self.server_configs[server_name] = {
            "command": command,
            "args": args
        }
        return session
    
    async def list_tools(self, server_name: Optional[str] = None) -> List[Tool]:
        """List available tools from one or all connected servers."""
        if server_name:
            session = self.sessions.get(server_name)
            if session:
                result = await session.list_tools()
                return result.tools
            return []
        
        # List from all servers
        all_tools = []
        for name, session in self.sessions.items():
            result = await session.list_tools()
            # Add server name to tool metadata
            for tool in result.tools:
                tool.metadata = tool.metadata or {}
                tool.metadata["server"] = name
            all_tools.extend(result.tools)
        return all_tools
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Call a tool on a specific MCP server."""
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"Not connected to server: {server_name}")
        
        # Call the tool
        try:
            from mcp.types import CallToolRequest
            request = CallToolRequest(name=tool_name, arguments=arguments)
            result = await session.call_tool(request)
        except ImportError:
            # Try direct call if Request types not available
            result = await session.call_tool(tool_name, arguments)
        return result
    
    async def list_resources(self, server_name: Optional[str] = None) -> List[Resource]:
        """List available resources from servers."""
        if server_name:
            session = self.sessions.get(server_name)
            if session:
                result = await session.list_resources()
                return result.resources
            return []
        
        # List from all servers
        all_resources = []
        for name, session in self.sessions.items():
            result = await session.list_resources()
            for resource in result.resources:
                resource.metadata = resource.metadata or {}
                resource.metadata["server"] = name
            all_resources.extend(result.resources)
        return all_resources
    
    async def read_resource(self, server_name: str, uri: str) -> List[TextContent]:
        """Read a resource from an MCP server."""
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"Not connected to server: {server_name}")
        
        try:
            from mcp.types import ReadResourceRequest
            request = ReadResourceRequest(uri=uri)
            result = await session.read_resource(request)
        except ImportError:
            # Try direct call if Request types not available
            result = await session.read_resource(uri)
        
        return result.contents if hasattr(result, 'contents') else result