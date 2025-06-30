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
MCP Server wrapper for VAC functionality.
This module exposes VAC streaming capabilities as MCP tools.
"""

from typing import Any, Sequence, Dict, List, Optional, Callable
import json
import asyncio
from functools import partial

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
except ImportError:
    Server = None
    Tool = None
    TextContent = None

from ..custom_logging import log
from ..streaming import start_streaming_chat_async


class VACMCPServer:
    """MCP Server that exposes VAC functionality as tools."""
    
    def __init__(self, stream_interpreter: Callable, vac_interpreter: Callable = None):
        """
        Initialize the VAC MCP Server.
        
        Args:
            stream_interpreter: The streaming interpreter function
            vac_interpreter: The static VAC interpreter function (optional)
        """
        if Server is None:
            raise ImportError("MCP server requires `pip install sunholo[anthropic]`")
        
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter
        self.server = Server("sunholo-vac-server")
        
        # Set up handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available VAC tools."""
            tools = [
                Tool(
                    name="vac_stream",
                    description="Stream responses from a Sunholo VAC (Virtual Agent Computer)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vector_name": {
                                "type": "string",
                                "description": "Name of the VAC to interact with"
                            },
                            "user_input": {
                                "type": "string", 
                                "description": "The user's question or input"
                            },
                            "chat_history": {
                                "type": "array",
                                "description": "Previous conversation history",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "human": {"type": "string"},
                                        "ai": {"type": "string"}
                                    }
                                },
                                "default": []
                            },
                            "stream_wait_time": {
                                "type": "number",
                                "description": "Time to wait between stream chunks",
                                "default": 7
                            },
                            "stream_timeout": {
                                "type": "number",
                                "description": "Maximum time to wait for response",
                                "default": 120
                            }
                        },
                        "required": ["vector_name", "user_input"]
                    }
                )
            ]
            
            # Add static VAC tool if interpreter is provided
            if self.vac_interpreter:
                tools.append(
                    Tool(
                        name="vac_query",
                        description="Query a Sunholo VAC (non-streaming)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "vector_name": {
                                    "type": "string",
                                    "description": "Name of the VAC to interact with"
                                },
                                "user_input": {
                                    "type": "string",
                                    "description": "The user's question or input"
                                },
                                "chat_history": {
                                    "type": "array",
                                    "description": "Previous conversation history",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "human": {"type": "string"},
                                            "ai": {"type": "string"}
                                        }
                                    },
                                    "default": []
                                }
                            },
                            "required": ["vector_name", "user_input"]
                        }
                    )
                )
            
            return tools
        
        @self.server.call_tool()
        async def call_tool(
            name: str,
            arguments: Any
        ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool calls for VAC interactions."""
            
            if name == "vac_stream":
                return await self._handle_vac_stream(arguments)
            elif name == "vac_query" and self.vac_interpreter:
                return await self._handle_vac_query(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_vac_stream(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Handle streaming VAC requests."""
        vector_name = arguments.get("vector_name")
        user_input = arguments.get("user_input")
        chat_history = arguments.get("chat_history", [])
        stream_wait_time = arguments.get("stream_wait_time", 7)
        stream_timeout = arguments.get("stream_timeout", 120)
        
        if not vector_name or not user_input:
            raise ValueError("Missing required arguments: vector_name and user_input")
        
        log.info(f"MCP streaming request for VAC '{vector_name}': {user_input}")
        
        try:
            # Collect streaming responses
            full_response = ""
            
            async for chunk in start_streaming_chat_async(
                question=user_input,
                vector_name=vector_name,
                qna_func_async=self.stream_interpreter,
                chat_history=chat_history,
                wait_time=stream_wait_time,
                timeout=stream_timeout
            ):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    full_response = chunk['answer']
                elif isinstance(chunk, str):
                    full_response += chunk
            
            return [
                TextContent(
                    type="text",
                    text=full_response or "No response generated"
                )
            ]
            
        except Exception as e:
            log.error(f"Error in MCP VAC stream: {str(e)}")
            return [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
    
    async def _handle_vac_query(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Handle non-streaming VAC requests."""
        vector_name = arguments.get("vector_name")
        user_input = arguments.get("user_input")
        chat_history = arguments.get("chat_history", [])
        
        if not vector_name or not user_input:
            raise ValueError("Missing required arguments: vector_name and user_input")
        
        log.info(f"MCP query request for VAC '{vector_name}': {user_input}")
        
        try:
            # Run in executor if not async
            if asyncio.iscoroutinefunction(self.vac_interpreter):
                result = await self.vac_interpreter(
                    question=user_input,
                    vector_name=vector_name,
                    chat_history=chat_history
                )
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    partial(
                        self.vac_interpreter,
                        question=user_input,
                        vector_name=vector_name,
                        chat_history=chat_history
                    )
                )
            
            # Extract answer from result
            if isinstance(result, dict):
                answer = result.get("answer", str(result))
            else:
                answer = str(result)
            
            return [
                TextContent(
                    type="text",
                    text=answer
                )
            ]
            
        except Exception as e:
            log.error(f"Error in MCP VAC query: {str(e)}")
            return [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
    
    def get_server(self) -> Server:
        """Get the underlying MCP server instance."""
        return self.server