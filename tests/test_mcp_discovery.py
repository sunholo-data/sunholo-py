"""Tests for sunholo.mcp.discovery module."""
import pytest

from sunholo.mcp.discovery import (
    MCPServerConfig,
    MCPDiscovery,
    MCP_PREFIX,
    EXTERNAL_MCP_TOOL,
    is_mcp_tool,
)


class TestMCPServerConfig:
    def test_basic_config(self):
        config = MCPServerConfig(server_id="search")
        assert config.server_id == "search"
        assert config.name == "search"
        assert config.url == ""
        assert config.command == ""
        assert config.args == []
        assert config.auto_discover is True

    def test_custom_config(self):
        config = MCPServerConfig(
            server_id="myserver",
            name="My Server",
            description="A test server",
            url="http://localhost:8080/mcp",
            tags=["search", "tools"],
        )
        assert config.name == "My Server"
        assert config.description == "A test server"
        assert config.url == "http://localhost:8080/mcp"
        assert config.tags == ["search", "tools"]

    def test_tool_id(self):
        config = MCPServerConfig(server_id="search")
        assert config.tool_id == "mcp_search"

    def test_to_dict(self):
        config = MCPServerConfig(server_id="test", name="Test Server")
        d = config.to_dict()
        assert d["server_id"] == "test"
        assert d["name"] == "Test Server"
        assert "url" in d
        assert "auto_discover" in d

    def test_stdio_config(self):
        config = MCPServerConfig(
            server_id="local",
            command="python",
            args=["-m", "my_mcp_server"],
        )
        assert config.command == "python"
        assert config.args == ["-m", "my_mcp_server"]


class TestMCPDiscovery:
    def test_register_server(self):
        discovery = MCPDiscovery()
        discovery.register_server(
            "search",
            name="Search Server",
            url="http://localhost:8080/mcp",
        )
        servers = discovery.list_servers()
        assert len(servers) == 1
        assert servers[0]["server_id"] == "search"
        assert servers[0]["name"] == "Search Server"

    def test_register_multiple_servers(self):
        discovery = MCPDiscovery()
        discovery.register_server("search", url="http://search/mcp")
        discovery.register_server("email", url="http://email/mcp")
        assert len(discovery.list_servers()) == 2

    def test_unregister_server(self):
        discovery = MCPDiscovery()
        discovery.register_server("search", url="http://search/mcp")
        discovery.unregister_server("search")
        assert len(discovery.list_servers()) == 0

    def test_unregister_nonexistent(self):
        discovery = MCPDiscovery()
        discovery.unregister_server("nonexistent")  # Should not raise

    def test_get_tool_info_not_found(self):
        discovery = MCPDiscovery()
        assert discovery.get_tool_info("mcp_unknown") is None

    def test_list_discovered_tools_empty(self):
        discovery = MCPDiscovery()
        assert discovery.list_discovered_tools() == []

    def test_get_tools_for_server_empty(self):
        discovery = MCPDiscovery()
        discovery.register_server("search", url="http://search/mcp")
        assert discovery.get_tools_for_server("search") == []

    def test_add_to_available_tools(self):
        discovery = MCPDiscovery()
        discovery.register_server("search", url="http://search/mcp")
        discovery.register_server("email", url="http://email/mcp")

        tools = discovery.add_to_available_tools(["existing_tool"])
        assert "existing_tool" in tools
        assert EXTERNAL_MCP_TOOL in tools
        assert "mcp_search" in tools
        assert "mcp_email" in tools

    def test_add_to_available_tools_no_duplicates(self):
        discovery = MCPDiscovery()
        discovery.register_server("search", url="http://search/mcp")

        tools = discovery.add_to_available_tools(
            [EXTERNAL_MCP_TOOL, "mcp_search"]
        )
        assert tools.count(EXTERNAL_MCP_TOOL) == 1
        assert tools.count("mcp_search") == 1

    def test_add_to_available_tools_empty(self):
        discovery = MCPDiscovery()
        tools = discovery.add_to_available_tools([])
        assert EXTERNAL_MCP_TOOL in tools


class TestIsMcpTool:
    def test_mcp_prefix(self):
        assert is_mcp_tool("mcp_search")
        assert is_mcp_tool("mcp_email_send")

    def test_external_mcp(self):
        assert is_mcp_tool(EXTERNAL_MCP_TOOL)

    def test_not_mcp(self):
        assert not is_mcp_tool("search")
        assert not is_mcp_tool("email")
        assert not is_mcp_tool("")

    def test_prefix_constant(self):
        assert MCP_PREFIX == "mcp_"
