#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from flask import Flask

# Import the classes under test
from sunholo.agents.flask.vac_routes import VACRoutes
from sunholo.mcp.mcp_manager import MCPClientManager


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return Flask(__name__)


@pytest.fixture
def mock_stream_interpreter():
    """Mock stream interpreter function."""
    def mock_func(question, vector_name, chat_history, **kwargs):
        return {"answer": f"Mock response to: {question}"}
    return mock_func


@pytest.fixture
def mock_vac_interpreter():
    """Mock VAC interpreter function."""
    def mock_func(question, vector_name, chat_history, **kwargs):
        return {"answer": f"Mock static response to: {question}"}
    return mock_func


@pytest.fixture
def mcp_servers_config():
    """Mock MCP server configuration."""
    return [
        {
            "name": "test_server",
            "command": "python",
            "args": ["-m", "test_mcp_server"]
        }
    ]


class TestMCPClientManager:
    """Test the MCPClientManager class."""
    
    def test_init(self):
        """Test MCPClientManager initialization."""
        manager = MCPClientManager()
        assert manager.sessions == {}
        assert manager.server_configs == {}
    
    @pytest.mark.asyncio
    async def test_connect_to_server(self):
        """Test connecting to an MCP server."""
        manager = MCPClientManager()
        
        # Mock the MCP client components
        with patch('sunholo.mcp.mcp_manager.stdio_client') as mock_stdio, \
             patch('sunholo.mcp.mcp_manager.ClientSession') as mock_session_class:
            
            # Setup mocks
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_stdio.return_value.__aenter__.return_value = (Mock(), Mock())
            
            # Test connection
            result = await manager.connect_to_server("test_server", "python", ["-m", "test"])
            
            # Verify
            assert result == mock_session
            assert "test_server" in manager.sessions
            assert manager.server_configs["test_server"]["command"] == "python"
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing tools from MCP servers."""
        manager = MCPClientManager()
        
        # Mock session with tools
        mock_session = AsyncMock()
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        mock_tool.metadata = {}
        mock_session.list_tools.return_value = [mock_tool]
        
        manager.sessions["test_server"] = mock_session
        
        # Test listing tools from specific server
        tools = await manager.list_tools("test_server")
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        
        # Test listing all tools
        all_tools = await manager.list_tools()
        assert len(all_tools) == 1
        assert all_tools[0].metadata["server"] == "test_server"
    
    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test calling a tool on an MCP server."""
        manager = MCPClientManager()
        
        # Mock session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_session.call_tool.return_value = mock_result
        manager.sessions["test_server"] = mock_session
        
        # Test calling tool
        result = await manager.call_tool("test_server", "test_tool", {"arg": "value"})
        
        assert result == mock_result
        mock_session.call_tool.assert_called_once_with("test_tool", {"arg": "value"})
    
    @pytest.mark.asyncio
    async def test_call_tool_server_not_found(self):
        """Test calling a tool on non-existent server."""
        manager = MCPClientManager()
        
        with pytest.raises(ValueError, match="Not connected to server: nonexistent"):
            await manager.call_tool("nonexistent", "test_tool", {})


class TestVACRoutes:
    """Test the VACRoutes class."""
    
    def test_init_basic(self, app, mock_stream_interpreter):
        """Test basic VACRoutes initialization."""
        vac_routes = VACRoutes(app, mock_stream_interpreter)
        
        assert vac_routes.app == app
        assert vac_routes.stream_interpreter == mock_stream_interpreter
        assert vac_routes.mcp_servers == []
        assert vac_routes.async_stream == False
    
    def test_init_with_mcp_servers(self, app, mock_stream_interpreter, mcp_servers_config):
        """Test VACRoutes initialization with MCP servers."""
        with patch('sunholo.agents.flask.vac_routes.MCPClientManager') as mock_manager_class, \
             patch('asyncio.create_task') as mock_create_task:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            vac_routes = VACRoutes(
                app, 
                mock_stream_interpreter,
                mcp_servers=mcp_servers_config
            )
            
            assert vac_routes.mcp_servers == mcp_servers_config
            assert vac_routes.mcp_client_manager == mock_manager
            mock_create_task.assert_called_once()
    
    def test_home_route(self, app, mock_stream_interpreter):
        """Test the home route."""
        vac_routes = VACRoutes(app, mock_stream_interpreter)
        
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            assert response.get_json() == "OK"
    
    def test_health_route(self, app, mock_stream_interpreter):
        """Test the health route."""
        vac_routes = VACRoutes(app, mock_stream_interpreter)
        
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            assert response.get_json() == {"status": "healthy"}
    
    @patch('sunholo.agents.flask.vac_routes.ConfigManager')
    def test_handle_process_vac(self, mock_config_manager, app, mock_vac_interpreter):
        """Test processing a VAC request."""
        # Mock ConfigManager
        mock_config = Mock()
        mock_config.configs_by_kind = {}
        mock_config.vacConfig.return_value = "test_model"
        mock_config_manager.return_value = mock_config
        
        vac_routes = VACRoutes(app, None, mock_vac_interpreter, add_langfuse_eval=False)
        
        with app.test_client() as client:
            response = client.post(
                '/vac/test_vector',
                json={
                    'user_input': 'Hello, world!',
                    'chat_history': []
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'answer' in data
            assert 'Hello, world!' in data['answer']
    
    def test_mcp_routes_registration(self, app, mock_stream_interpreter, mcp_servers_config):
        """Test that MCP routes are registered when MCP servers are provided."""
        with patch('sunholo.agents.flask.vac_routes.MCPClientManager'), \
             patch('asyncio.create_task'):
            vac_routes = VACRoutes(
                app, 
                mock_stream_interpreter,
                mcp_servers=mcp_servers_config
            )
            
            # Check that MCP routes are registered
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            assert '/mcp/tools' in rules
            assert '/mcp/tools/<server_name>' in rules
            assert '/mcp/call' in rules
            assert '/mcp/resources' in rules
            assert '/mcp/resources/read' in rules
    
    @patch('sunholo.agents.flask.vac_routes.MCPClientManager')
    @patch('asyncio.create_task')
    def test_mcp_list_tools_endpoint(self, mock_create_task, mock_manager_class, app, mock_stream_interpreter, mcp_servers_config):
        """Test the MCP list tools endpoint."""
        # Setup mock manager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # Mock async method
        async def mock_list_tools(server_name=None):
            mock_tool = Mock()
            mock_tool.name = "test_tool"
            mock_tool.description = "Test tool description"
            mock_tool.inputSchema = {"type": "object"}
            mock_tool.metadata = {"server": "test_server"}
            return [mock_tool]
        
        mock_manager.list_tools = mock_list_tools
        
        vac_routes = VACRoutes(
            app, 
            mock_stream_interpreter,
            mcp_servers=mcp_servers_config
        )
        
        with app.test_client() as client:
            response = client.get('/mcp/tools')
            assert response.status_code == 200
            data = response.get_json()
            assert 'tools' in data
            assert len(data['tools']) == 1
            assert data['tools'][0]['name'] == 'test_tool'
    
    @patch('sunholo.agents.flask.vac_routes.MCPClientManager')
    @patch('asyncio.create_task')
    def test_mcp_call_tool_endpoint(self, mock_create_task, mock_manager_class, app, mock_stream_interpreter, mcp_servers_config):
        """Test the MCP call tool endpoint."""
        # Setup mock manager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # Mock async method
        async def mock_call_tool(server_name, tool_name, arguments):
            mock_result = Mock()
            mock_result.content = Mock()
            mock_result.content.text = f"Tool {tool_name} executed with {arguments}"
            return mock_result
        
        mock_manager.call_tool = mock_call_tool
        
        vac_routes = VACRoutes(
            app, 
            mock_stream_interpreter,
            mcp_servers=mcp_servers_config
        )
        
        with app.test_client() as client:
            response = client.post(
                '/mcp/call',
                json={
                    'server': 'test_server',
                    'tool': 'test_tool',
                    'arguments': {'param': 'value'}
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'result' in data
            assert 'test_tool executed' in data['result']
    
    def test_openai_compatible_endpoint(self, app, mock_vac_interpreter):
        """Test OpenAI compatible endpoint."""
        with patch('sunholo.agents.flask.vac_routes.ConfigManager'):
            vac_routes = VACRoutes(app, None, mock_vac_interpreter, add_langfuse_eval=False)
            
            # Mock the before_request handler to skip auth
            app.before_request_funcs = {}
            
            with app.test_client() as client:
                response = client.post(
                    '/openai/v1/chat/completions',
                    json={
                        'model': 'test_model',
                        'messages': [
                            {'role': 'user', 'content': 'Hello AI'}
                        ]
                    },
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                data = response.get_json()
                assert 'choices' in data
                assert data['choices'][0]['message']['role'] == 'assistant'
    
    def test_vac_interpreter_default(self, app, mock_stream_interpreter):
        """Test the default VAC interpreter behavior."""
        vac_routes = VACRoutes(app, mock_stream_interpreter)
        
        result = vac_routes.vac_interpreter_default(
            question="Test question",
            vector_name="test_vector",
            chat_history=[]
        )
        
        assert result is not None
        # The default interpreter should call the stream interpreter with a NoOpCallback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])