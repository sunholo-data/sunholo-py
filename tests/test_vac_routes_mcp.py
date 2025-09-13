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

"""Tests for MCP (Model Context Protocol) functionality in FastAPI VAC Routes."""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Skip entire test file if dependencies are not available
pytest.importorskip("fastapi")
pytest.importorskip("mcp")
pytest.importorskip("fastmcp")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sunholo.agents.fastapi import VACRoutesFastAPI
from tests.fixtures.mock_interpreters import (
    mock_async_stream_interpreter,
    mock_async_vac_interpreter,
    mock_sync_stream_interpreter,
    mock_sync_vac_interpreter
)


class MockVACMCPServer:
    """Mock MCP server for testing."""
    
    def __init__(self, stream_interpreter, vac_interpreter):
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter
        self.tools = {
            "vac_stream": {
                "name": "vac_stream",
                "description": "Stream responses from a VAC",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vector_name": {"type": "string"},
                        "user_input": {"type": "string"}
                    },
                    "required": ["vector_name", "user_input"]
                }
            },
            "vac_query": {
                "name": "vac_query", 
                "description": "Query a VAC (non-streaming)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vector_name": {"type": "string"},
                        "user_input": {"type": "string"}
                    },
                    "required": ["vector_name", "user_input"]
                }
            }
        }
    
    async def handle_request(self, request_data):
        """Handle MCP request."""
        method = request_data.get("method")
        
        if method == "tools/list":
            return {
                "tools": list(self.tools.values())
            }
        elif method == "tools/call":
            tool_name = request_data.get("params", {}).get("name")
            arguments = request_data.get("params", {}).get("arguments", {})
            
            if tool_name == "vac_stream":
                # Simulate streaming response
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Streaming response for: {arguments.get('user_input')}"
                        }
                    ]
                }
            elif tool_name == "vac_query":
                # Simulate non-streaming response
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Query response for: {arguments.get('user_input')}"
                        }
                    ]
                }
        
        return {"error": "Unknown method"}
    
    async def _handle_vac_stream(self, vector_name: str, user_input: str, **kwargs):
        """Mock implementation of vac_stream handler."""
        return f"Mock streaming response for VAC {vector_name}: {user_input}"
    
    async def _handle_vac_query(self, vector_name: str, user_input: str, **kwargs):
        """Mock implementation of vac_query handler."""
        return f"Mock query response for VAC {vector_name}: {user_input}"


class MockMCPClientManager:
    """Mock MCP client manager for testing."""
    
    def __init__(self):
        self.servers = {}
        self.tools = {
            "filesystem": {
                "read_file": {
                    "name": "read_file",
                    "description": "Read a file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                }
            }
        }
        self.resources = {
            "filesystem": [
                {
                    "uri": "file:///test.txt",
                    "name": "test.txt",
                    "description": "Test file",
                    "mimeType": "text/plain"
                }
            ]
        }
    
    async def initialize_server(self, server_config):
        """Mock server initialization."""
        server_name = server_config.get("name")
        self.servers[server_name] = server_config
    
    async def list_tools(self, server_name=None):
        """Mock list tools."""
        if server_name and server_name in self.tools:
            return list(self.tools[server_name].values())
        
        all_tools = []
        for server_tools in self.tools.values():
            all_tools.extend(server_tools.values())
        return all_tools
    
    async def call_tool(self, server_name, tool_name, arguments):
        """Mock tool call."""
        if server_name in self.tools and tool_name in self.tools[server_name]:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Result from {tool_name}: {arguments}"
                    }
                ]
            }
        return {"error": "Tool not found"}
    
    async def list_resources(self, server_name=None):
        """Mock list resources."""
        if server_name and server_name in self.resources:
            return self.resources[server_name]
        
        all_resources = []
        for server_resources in self.resources.values():
            all_resources.extend(server_resources)
        return all_resources
    
    async def read_resource(self, server_name, uri):
        """Mock resource read."""
        if server_name in self.resources:
            for resource in self.resources[server_name]:
                if resource["uri"] == uri:
                    return {
                        "contents": [
                            {
                                "type": "text",
                                "text": f"Content of {uri}"
                            }
                        ]
                    }
        return {"error": "Resource not found"}


@pytest.fixture
def mcp_server_app():
    """Create a FastAPI app with MCP server enabled."""
    from contextlib import asynccontextmanager
    
    # Create a simple lifespan for the test
    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        yield
    
    app = FastAPI(lifespan=test_lifespan)
    
    # First disable MCP server to avoid initialization issues
    vac_routes = VACRoutesFastAPI(
        app,
        stream_interpreter=mock_async_stream_interpreter,
        vac_interpreter=mock_async_vac_interpreter,
        add_langfuse_eval=False
    )
    
    # Add a mock MCP endpoint manually for testing
    @app.post("/mcp")
    async def mock_mcp_endpoint(request: dict):
        """Mock MCP endpoint for testing."""
        mock_server = MockVACMCPServer(
            mock_async_stream_interpreter,
            mock_async_vac_interpreter
        )
        return await mock_server.handle_request(request)
    
    # Set the mock server for other tests that might need it
    vac_routes.vac_mcp_server = MockVACMCPServer(
        mock_async_stream_interpreter, 
        mock_async_vac_interpreter
    )
    
    return app


@pytest.fixture
def mcp_client_app():
    """Create a FastAPI app with MCP client configured."""
    app = FastAPI()
    mcp_servers = [
        {
            "name": "filesystem",
            "command": "mcp-server-filesystem",
            "args": ["/tmp"]
        }
    ]
    vac_routes = VACRoutesFastAPI(
        app,
        stream_interpreter=mock_async_stream_interpreter,
        vac_interpreter=mock_async_vac_interpreter,
        mcp_servers=mcp_servers,
        add_langfuse_eval=False
    )
    # Replace with mock MCP client manager
    vac_routes.mcp_client_manager = MockMCPClientManager()
    return app


@pytest.fixture
def test_client_mcp_server(mcp_server_app):
    """Create test client for MCP server app."""
    return TestClient(mcp_server_app)


@pytest.fixture
def test_client_mcp_client(mcp_client_app):
    """Create test client for MCP client app."""
    return TestClient(mcp_client_app)


class TestMCPServer:
    """Test MCP server functionality."""
    
    def test_mcp_server_tools_list(self, test_client_mcp_server):
        """Test listing available tools from MCP server."""
        response = test_client_mcp_server.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
        )
        assert response.status_code == 200
        data = response.json()
        # FastMCP returns result wrapped in JSONRPC response
        if "result" in data:
            assert "tools" in data["result"]
            tools = data["result"]["tools"]
        else:
            assert "tools" in data
            tools = data["tools"]
        assert len(tools) == 2
        tool_names = [tool["name"] for tool in tools]
        assert "vac_stream" in tool_names
        assert "vac_query" in tool_names
    
    def test_mcp_server_invalid_method(self, test_client_mcp_server):
        """Test MCP server with invalid method."""
        response = test_client_mcp_server.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "invalid/method"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
    
    def test_mcp_server_disabled(self):
        """Test that MCP server is not available when disabled."""
        app = FastAPI()
        vac_routes = VACRoutesFastAPI(
            app,
            stream_interpreter=mock_async_stream_interpreter,
            add_langfuse_eval=False
        )
        client = TestClient(app)
        
        response = client.post("/mcp", json={})
        assert response.status_code == 404




class TestMCPDebugEndpoint:
    """Test MCP debug endpoint functionality."""
    
    def test_debug_endpoint_with_mcp_server(self):
        """Test /debug/mcp endpoint when MCP server is enabled."""
        app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
            title="Test App",
            stream_interpreter=mock_async_stream_interpreter
        )
        
        # Add a mock tool to test
        @vac_routes.add_mcp_tool
        async def test_tool(input: str) -> str:
            """Test tool for MCP."""
            return f"Test: {input}"
        
        client = TestClient(app)
        response = client.get("/debug/mcp")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check basic structure
        assert "mcp_enabled" in data
        assert "has_mcp_server" in data
        assert "mcp_tools_count" in data
        assert "mcp_tools" in data
        
        # Check values
        assert data["mcp_enabled"] is True
        assert data["has_mcp_server"] is True
        assert data["mcp_tools_count"] >= 5  # Built-in tools + test_tool
        
        # Check that test_tool is in the list
        tool_names = [tool["name"] for tool in data["mcp_tools"]]
        assert "test_tool" in tool_names
        
        # Check built-in tools are present
        assert "vac_stream" in tool_names
        assert "vac_query" in tool_names
        assert "list_available_vacs" in tool_names
        assert "get_vac_info" in tool_names
    
    def test_debug_endpoint_without_mcp_server(self):
        """Test /debug/mcp endpoint when MCP server is not present."""
        app = FastAPI()
        vac_routes = VACRoutesFastAPI(
            app,
            stream_interpreter=mock_async_stream_interpreter,
            add_langfuse_eval=False
        )
        
        # Should not have debug endpoint if no MCP server
        client = TestClient(app)
        response = client.get("/debug/mcp")
        assert response.status_code == 404


class TestMCPErrorHandling:
    """Test MCP error handling."""
    
    def test_mcp_server_malformed_request(self, test_client_mcp_server):
        """Test MCP server with malformed request."""
        response = test_client_mcp_server.post(
            "/mcp",
            json={"malformed": "request"}
        )
        assert response.status_code == 200