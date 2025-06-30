#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0

"""
Integration test for MCP server functionality.
This test will fail until the async queue issue is fixed.
"""

import pytest
import json
import requests
import time

class TestMCPIntegration:
    """Test MCP server integration with actual HTTP requests."""
    
    @pytest.fixture
    def server_url(self):
        """MCP server URL - assumes server is running on localhost:1956."""
        return "http://127.0.0.1:1956"
    
    def test_mcp_server_info(self, server_url):
        """Test MCP server info endpoint works."""
        response = requests.get(f"{server_url}/mcp")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "sunholo-vac-server"
        assert data["transport"] == "http"
        assert "vac_stream" in data["tools"]
        assert "vac_query" in data["tools"]
    
    def test_mcp_tools_list_jsonrpc(self, server_url):
        """Test MCP tools/list via JSON-RPC protocol."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        response = requests.post(
            f"{server_url}/mcp",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # This test will fail until the async queue issue is fixed
        assert "error" not in data, f"Expected success but got error: {data.get('error', {}).get('message', 'Unknown error')}"
        assert "result" in data
        assert "tools" in data["result"]
        
        # Verify tools are present
        tools = data["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]
        assert "vac_stream" in tool_names
        assert "vac_query" in tool_names
    
    def test_mcp_tool_call_jsonrpc(self, server_url):
        """Test MCP tool call via JSON-RPC protocol."""
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "vac_stream",
                "arguments": {
                    "vector_name": "test",
                    "user_input": "Hello, this is a test",
                    "chat_history": [],
                    "stream_wait_time": 1,
                    "stream_timeout": 10
                }
            }
        }
        
        response = requests.post(
            f"{server_url}/mcp",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # This test will fail until the async queue issue is fixed
        assert "error" not in data, f"Expected success but got error: {data.get('error', {}).get('message', 'Unknown error')}"
        assert "result" in data
        assert "content" in data["result"]
        
        # Verify content structure
        content = data["result"]["content"]
        assert isinstance(content, list)
        assert len(content) > 0
        assert content[0]["type"] == "text"
        assert "text" in content[0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])