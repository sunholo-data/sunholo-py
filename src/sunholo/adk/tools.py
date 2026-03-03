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
MCP tool decorator pattern for ADK agents.

Provides a decorator to wrap remote MCP server tools for use in ADK agents.
Each decorated function becomes an ADK-compatible tool that calls a remote
MCP server via the FastMCP client.

Usage:
    from sunholo.adk.tools import mcp_tool

    @mcp_tool("search_documents", mcp_url_env="SHAREPOINT_MCP_URL")
    async def search_documents(query: str, limit: int = 10, tool_context=None):
        '''Search documents in SharePoint.'''
        pass  # Implementation provided by MCP server

    # Or with explicit URL:
    @mcp_tool("verify_code", mcp_url="http://localhost:8080")
    async def verify_code(code: str, tool_context=None):
        '''Verify a code.'''
        pass
"""
from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

try:
    from fastmcp import Client as FastMCPClient
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False


def mcp_tool(
    tool_name: str,
    *,
    mcp_url: str = "",
    mcp_url_env: str = "",
    requires_auth: bool = False,
    auth_state_key: str = "user:auth_token",
) -> Callable:
    """Decorator to create an ADK tool that delegates to a remote MCP server.

    The decorated function's signature defines the tool's parameters for ADK,
    but the actual execution is handled by calling the named tool on the
    remote MCP server.

    Args:
        tool_name: The name of the tool on the MCP server.
        mcp_url: Explicit MCP server URL.
        mcp_url_env: Environment variable containing the MCP server URL.
            Takes precedence over mcp_url if the env var is set.
        requires_auth: Whether the tool requires an auth token from session state.
        auth_state_key: Session state key containing the auth token.

    Returns:
        Decorator that wraps a function as an MCP-backed ADK tool.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not FASTMCP_AVAILABLE:
                raise ImportError(
                    "fastmcp is required for MCP tools. "
                    "Install with: pip install sunholo[adk]"
                )

            # Resolve MCP server URL
            url = ""
            if mcp_url_env:
                url = os.getenv(mcp_url_env, "")
            if not url:
                url = mcp_url
            if not url:
                raise ValueError(
                    f"MCP server URL not configured for tool '{tool_name}'. "
                    f"Set environment variable '{mcp_url_env}' or provide mcp_url."
                )

            # Extract tool_context if present (ADK convention)
            tool_context = kwargs.pop("tool_context", None)

            # Get auth token from session state if required
            headers = {}
            if requires_auth and tool_context:
                state = getattr(tool_context, "state", {})
                if callable(getattr(state, "get", None)):
                    token = state.get(auth_state_key, "")
                else:
                    token = getattr(state, auth_state_key, "")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            # Build tool arguments from kwargs (excluding internal params)
            tool_args = {k: v for k, v in kwargs.items() if v is not None}

            logger.info("Calling MCP tool '%s' on %s", tool_name, url)

            try:
                async with FastMCPClient(url) as client:
                    result = await client.call_tool(tool_name, tool_args)
                return result
            except Exception as e:
                logger.error("MCP tool '%s' failed: %s", tool_name, e)
                raise

        # Preserve the original function's metadata for ADK tool registration
        wrapper._mcp_tool_name = tool_name
        wrapper._mcp_url_env = mcp_url_env
        wrapper._mcp_url = mcp_url
        return wrapper

    return decorator
