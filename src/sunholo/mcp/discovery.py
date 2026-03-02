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
Dynamic MCP tool discovery and registration.

Connects to MCP servers, discovers available tools, and registers them
for use in tool orchestration and permission systems.

Supports:
- Server registry with connection configs
- Auto-discovery of tools from connected servers
- Tool ID naming convention (mcp_{server_id})
- Integration with ExtensibleMCPServer and MCPClientManager

Usage:
    from sunholo.mcp.discovery import MCPDiscovery

    discovery = MCPDiscovery()
    discovery.register_server("search", url="http://localhost:8080/mcp")

    # Discover tools on registered servers
    tools = await discovery.discover_all()

    # Check if a tool ID is an MCP tool
    if discovery.is_mcp_tool("mcp_search"):
        info = discovery.get_tool_info("mcp_search")
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# MCP tool ID prefix convention
MCP_PREFIX = "mcp_"
EXTERNAL_MCP_TOOL = "external_mcp"


class MCPServerConfig:
    """Configuration for an MCP server.

    Args:
        server_id: Unique identifier for this server.
        name: Human-readable server name.
        description: Description of what this server provides.
        url: HTTP/SSE URL for the MCP server.
        command: Command for stdio transport (alternative to url).
        args: Command arguments for stdio transport.
        auth: Authentication token or method.
        tags: Categorization tags.
        auto_discover: Whether to discover tools on startup.
    """

    def __init__(
        self,
        server_id: str,
        name: str = "",
        description: str = "",
        url: str = "",
        command: str = "",
        args: List[str] | None = None,
        auth: str = "",
        tags: List[str] | None = None,
        auto_discover: bool = True,
    ):
        self.server_id = server_id
        self.name = name or server_id
        self.description = description
        self.url = url
        self.command = command
        self.args = args or []
        self.auth = auth
        self.tags = tags or []
        self.auto_discover = auto_discover

    @property
    def tool_id(self) -> str:
        """The tool ID for this server (mcp_{server_id})."""
        return f"{MCP_PREFIX}{self.server_id}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "server_id": self.server_id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "command": self.command,
            "args": self.args,
            "tags": self.tags,
            "auto_discover": self.auto_discover,
        }


class MCPDiscovery:
    """Discovers and manages MCP tools from multiple servers.

    Maintains a registry of MCP servers and their discovered tools.
    Tools are identified by the convention: mcp_{server_id}.

    Usage:
        discovery = MCPDiscovery()
        discovery.register_server("search", url="http://localhost:8080/mcp")
        tools = await discovery.discover_all()
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._discovered_tools: Dict[str, Dict[str, Any]] = {}

    def register_server(
        self,
        server_id: str,
        name: str = "",
        description: str = "",
        url: str = "",
        command: str = "",
        args: List[str] | None = None,
        auth: str = "",
        tags: List[str] | None = None,
        auto_discover: bool = True,
    ) -> None:
        """Register an MCP server for discovery.

        Args:
            server_id: Unique identifier.
            name: Human-readable name.
            description: Server description.
            url: HTTP/SSE URL.
            command: Command for stdio transport.
            args: Command arguments.
            auth: Authentication token.
            tags: Categorization tags.
            auto_discover: Discover tools on startup.
        """
        self._servers[server_id] = MCPServerConfig(
            server_id=server_id,
            name=name,
            description=description,
            url=url,
            command=command,
            args=args,
            auth=auth,
            tags=tags,
            auto_discover=auto_discover,
        )

    def unregister_server(self, server_id: str) -> None:
        """Remove a server from the registry."""
        self._servers.pop(server_id, None)
        # Remove discovered tools for this server
        prefix = f"{MCP_PREFIX}{server_id}"
        to_remove = [k for k in self._discovered_tools if k.startswith(prefix)]
        for k in to_remove:
            del self._discovered_tools[k]

    def list_servers(self) -> List[Dict[str, Any]]:
        """List all registered servers."""
        return [s.to_dict() for s in self._servers.values()]

    async def discover_server(self, server_id: str) -> List[Dict[str, Any]]:
        """Discover tools on a specific server.

        Connects to the server via MCPClientManager and lists
        available tools.

        Args:
            server_id: Server to discover.

        Returns:
            List of discovered tool info dicts.
        """
        if server_id not in self._servers:
            logger.warning("Unknown server: %s", server_id)
            return []

        config = self._servers[server_id]

        try:
            from sunholo.mcp import MCPClientManager
            if MCPClientManager is None:
                logger.warning("MCPClientManager not available")
                return []

            manager = MCPClientManager()

            # Connect based on transport type
            if config.command:
                await manager.connect_to_server(
                    server_id, config.command, config.args
                )
            elif config.url:
                # For HTTP/SSE servers, connect via URL
                await manager.connect_to_server(
                    server_id, "npx", ["-y", "mcp-remote", config.url]
                )
            else:
                logger.warning("No connection method for server: %s", server_id)
                return []

            # List tools
            tools = await manager.list_tools(server_id)
            discovered = []

            for tool in tools:
                tool_name = tool.get("name", "")
                tool_id = f"{MCP_PREFIX}{server_id}_{tool_name}" if tool_name else config.tool_id

                info = {
                    "tool_id": tool_id,
                    "server_id": server_id,
                    "name": tool_name,
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {}),
                    "server_name": config.name,
                }
                self._discovered_tools[tool_id] = info
                discovered.append(info)

            logger.info(
                "Discovered %d tools from server %s", len(discovered), server_id
            )
            return discovered

        except Exception as e:
            logger.error("Failed to discover tools on %s: %s", server_id, e)
            return []

    async def discover_all(self) -> List[Dict[str, Any]]:
        """Discover tools on all registered servers with auto_discover=True.

        Returns:
            List of all discovered tool info dicts.
        """
        all_tools = []
        for server_id, config in self._servers.items():
            if config.auto_discover:
                tools = await self.discover_server(server_id)
                all_tools.extend(tools)
        return all_tools

    def get_tool_info(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a specific MCP tool.

        Args:
            tool_id: Tool ID (e.g. "mcp_search" or "mcp_search_query").

        Returns:
            Tool info dict, or None if not found.
        """
        return self._discovered_tools.get(tool_id)

    def get_tools_for_server(self, server_id: str) -> List[Dict[str, Any]]:
        """Get all discovered tools for a server."""
        prefix = f"{MCP_PREFIX}{server_id}"
        return [
            info for tool_id, info in self._discovered_tools.items()
            if tool_id.startswith(prefix)
        ]

    def list_discovered_tools(self) -> List[Dict[str, Any]]:
        """List all discovered tools across all servers."""
        return list(self._discovered_tools.values())

    def add_to_available_tools(self, available_tools: List[str]) -> List[str]:
        """Add MCP tool IDs to an available tools list.

        Adds the external_mcp generic tool and per-server tool IDs.

        Args:
            available_tools: Existing available tools list.

        Returns:
            Extended list with MCP tools added.
        """
        result = list(available_tools)
        if EXTERNAL_MCP_TOOL not in result:
            result.append(EXTERNAL_MCP_TOOL)
        for server_id in self._servers:
            tool_id = f"{MCP_PREFIX}{server_id}"
            if tool_id not in result:
                result.append(tool_id)
        return result


def is_mcp_tool(tool_id: str) -> bool:
    """Check if a tool ID represents an MCP tool.

    Args:
        tool_id: Tool identifier string.

    Returns:
        True if this is an MCP tool (external_mcp or mcp_* prefix).
    """
    return tool_id == EXTERNAL_MCP_TOOL or tool_id.startswith(MCP_PREFIX)
