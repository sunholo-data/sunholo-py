"""
Proper MCP integration for VACRoutes using the official MCP Python SDK.
This shows how to integrate MCP servers with your Flask/VACRoutes application.
"""

from typing import Dict, Any, List, Optional

# Official MCP imports
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import Tool, Resource, TextContent, CallToolResult


class MCPClientManager:
    """Manages MCP client connections to various MCP servers."""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.server_configs: Dict[str, Dict[str, Any]] = {}
        
    async def connect_to_server(self, server_name: str, command: str, args: List[str] = None) -> ClientSession:
        """Connect to an MCP server via stdio."""
        if server_name in self.sessions:
            return self.sessions[server_name]
        
        # Create server parameters
        server_params = StdioServerParameters(
            command=command,
            args=args or []
        )
        
        # Connect to the server
        async with stdio_client(server_params) as (read, write):
            # Create and initialize client session directly
            session = ClientSession(read, write)
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
                return await session.list_tools()
            return []
        
        # List from all servers
        all_tools = []
        for name, session in self.sessions.items():
            tools = await session.list_tools()
            # Add server name to tool metadata
            for tool in tools:
                tool.metadata = tool.metadata or {}
                tool.metadata["server"] = name
            all_tools.extend(tools)
        return all_tools
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Call a tool on a specific MCP server."""
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"Not connected to server: {server_name}")
        
        # Call the tool
        result = await session.call_tool(tool_name, arguments)
        return result
    
    async def list_resources(self, server_name: Optional[str] = None) -> List[Resource]:
        """List available resources from servers."""
        if server_name:
            session = self.sessions.get(server_name)
            if session:
                return await session.list_resources()
            return []
        
        # List from all servers
        all_resources = []
        for name, session in self.sessions.items():
            resources = await session.list_resources()
            for resource in resources:
                resource.metadata = resource.metadata or {}
                resource.metadata["server"] = name
            all_resources.extend(resources)
        return all_resources
    
    async def read_resource(self, server_name: str, uri: str) -> List[TextContent]:
        """Read a resource from an MCP server."""
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"Not connected to server: {server_name}")
        
        result = await session.read_resource(uri)
        return result.contents