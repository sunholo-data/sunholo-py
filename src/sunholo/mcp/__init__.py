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

"""MCP (Model Context Protocol) integration for Sunholo."""

try:
    from .mcp_manager import MCPClientManager
except ImportError as e:
    print(f"Warning: MCPClientManager not available - {e}")
    MCPClientManager = None

try:
    from .vac_mcp_server import VACMCPServer
except ImportError as e:
    print(f"Warning: VACMCPServer not available - {e}")
    VACMCPServer = None

# SSE utilities are always available
from .sse_utils import parse_sse_response, is_sse_response, extract_sse_data

__all__ = [
    'MCPClientManager', 
    'VACMCPServer',
    'parse_sse_response',
    'is_sse_response', 
    'extract_sse_data'
]