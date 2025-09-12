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

import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Skip entire test file if FastAPI is not available
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.sunholo.agents.fastapi.vac_routes import VACRoutesFastAPI, VACRequest
from tests.fixtures.mock_interpreters import (
    mock_async_stream_interpreter,
    mock_sync_stream_interpreter,
    mock_async_vac_interpreter,
    mock_sync_vac_interpreter,
    mock_async_stream_with_heartbeat,
    mock_async_stream_with_error,
    mock_sync_stream_with_timeout
)


@pytest.fixture
def fastapi_app_async():
    """Create a FastAPI app with async interpreters."""
    app = FastAPI()
    vac_routes = VACRoutesFastAPI(
        app,
        stream_interpreter=mock_async_stream_interpreter,
        vac_interpreter=mock_async_vac_interpreter,
        enable_mcp_server=False,
        add_langfuse_eval=False
    )
    return app


@pytest.fixture
def fastapi_app_sync():
    """Create a FastAPI app with sync interpreters."""
    app = FastAPI()
    vac_routes = VACRoutesFastAPI(
        app,
        stream_interpreter=mock_sync_stream_interpreter,
        vac_interpreter=mock_sync_vac_interpreter,
        enable_mcp_server=False,
        add_langfuse_eval=False
    )
    return app


@pytest.fixture
def test_client_async(fastapi_app_async):
    """Create test client for async app."""
    return TestClient(fastapi_app_async)


@pytest.fixture
def test_client_sync(fastapi_app_sync):
    """Create test client for sync app."""
    return TestClient(fastapi_app_sync)


class TestVACRoutesFastAPI:
    """Test suite for VACRoutesFastAPI."""
    
    def test_health_endpoint(self, test_client_async):
        """Test health check endpoint."""
        response = test_client_async.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_home_endpoint(self, test_client_async):
        """Test home endpoint."""
        response = test_client_async.get("/")
        assert response.status_code == 200
        assert response.json() == "OK"
    
    @pytest.mark.asyncio
    @patch('src.sunholo.agents.fastapi.vac_routes.ConfigManager')
    @patch('src.sunholo.agents.fastapi.vac_routes.extract_chat_history_async_cached')
    @patch('src.sunholo.agents.fastapi.vac_routes.archive_qa')
    async def test_async_streaming_plain(self, mock_archive, mock_extract, mock_config, test_client_async):
        """Test async streaming with plain text response."""
        # Setup mocks
        mock_config.return_value = MagicMock()
        mock_extract.return_value = []
        mock_archive.return_value = AsyncMock()
        
        # Make request
        request_data = {
            "user_input": "Test question",
            "chat_history": [],
            "stream_wait_time": 1,
            "stream_timeout": 10
        }
        
        response = test_client_async.post(
            "/vac/streaming/test_vac",
            json=request_data
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Check streaming content
        content = response.text
        assert "Hello from async interpreter!" in content
        assert "Test question" in content
    
    
    
    
    
    def test_openai_health(self, test_client_async):
        """Test OpenAI health endpoint."""
        response = test_client_async.get("/openai/health")
        assert response.status_code == 200
        assert response.json() == {"message": "Success"}
    
    
    
    def test_vac_request_model(self):
        """Test VACRequest model validation."""
        # Valid request
        request = VACRequest(
            user_input="Test",
            chat_history=[],
            stream_wait_time=5,
            stream_timeout=30
        )
        assert request.user_input == "Test"
        assert request.stream_wait_time == 5
        
        # Default values
        request = VACRequest(user_input="Test")
        assert request.chat_history is None
        assert request.stream_wait_time == 7
        assert request.stream_timeout == 120
    
    @pytest.mark.asyncio
    async def test_streaming_with_heartbeat(self):
        """Test streaming with heartbeat tokens."""
        app = FastAPI()
        vac_routes = VACRoutesFastAPI(
            app,
            stream_interpreter=mock_async_stream_with_heartbeat,
            enable_mcp_server=False,
            add_langfuse_eval=False
        )
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            request_data = {
                "user_input": "Test heartbeat",
                "chat_history": [],
                "stream_wait_time": 1,
                "stream_timeout": 10
            }
            
            with patch('src.sunholo.agents.fastapi.vac_routes.ConfigManager'):
                with patch('src.sunholo.agents.fastapi.vac_routes.extract_chat_history_async_cached', return_value=[]):
                    with patch('src.sunholo.agents.fastapi.vac_routes.archive_qa', new_callable=AsyncMock):
                        response = await client.post(
                            "/vac/streaming/test_vac",
                            json=request_data
                        )
                        
                        assert response.status_code == 200
                        # Heartbeat tokens should be processed
                        content = response.text
                        assert "Starting response..." in content
    
    
    def test_interpreter_detection(self):
        """Test that sync/async interpreter detection works correctly."""
        app = FastAPI()
        
        # Test async detection
        vac_routes_async = VACRoutesFastAPI(
            app,
            stream_interpreter=mock_async_stream_interpreter,
            vac_interpreter=mock_async_vac_interpreter
        )
        assert vac_routes_async.stream_is_async is True
        assert vac_routes_async.vac_is_async is True
        
        # Test sync detection
        vac_routes_sync = VACRoutesFastAPI(
            app,
            stream_interpreter=mock_sync_stream_interpreter,
            vac_interpreter=mock_sync_vac_interpreter
        )
        assert vac_routes_sync.stream_is_async is False
        assert vac_routes_sync.vac_is_async is False
    
    def test_mcp_server_disabled(self, test_client_async):
        """Test that MCP server endpoints return 404 when disabled."""
        response = test_client_async.post("/mcp")
        assert response.status_code == 404
        
        response = test_client_async.get("/mcp")
        assert response.status_code == 404
    
    def test_a2a_agent_disabled(self, test_client_async):
        """Test that A2A agent endpoints return 404 when disabled."""
        response = test_client_async.get("/.well-known/agent.json")
        assert response.status_code == 404
        
        response = test_client_async.post("/a2a/tasks/send")
        assert response.status_code == 404