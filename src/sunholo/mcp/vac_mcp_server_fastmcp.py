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
FastMCP-based MCP Server wrapper for VAC functionality.
This module exposes VAC streaming capabilities as MCP tools using FastMCP.
"""

from typing import Any, Callable, Dict, List, Optional
import asyncio
from functools import partial

from fastmcp import FastMCP

from ..custom_logging import log
from ..streaming import start_streaming_chat_async


class VACMCPServer:
    """FastMCP Server that exposes VAC functionality as tools."""
    
    def __init__(self, stream_interpreter: Callable, vac_interpreter: Callable = None):
        """
        Initialize the VAC MCP Server using FastMCP.
        
        Args:
            stream_interpreter: The streaming interpreter function
            vac_interpreter: The static VAC interpreter function (optional)
        """
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter
        
        # Initialize FastMCP server
        self.server = FastMCP("sunholo-vac-server")
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register VAC tools with FastMCP."""
        
        @self.server.tool
        async def vac_stream(
            vector_name: str,
            user_input: str,
            chat_history: List[Dict[str, str]] = None,
            stream_wait_time: float = 7,
            stream_timeout: float = 120
        ) -> str:
            """
            Stream responses from a Sunholo VAC (Virtual Agent Computer).
            
            Args:
                vector_name: Name of the VAC to interact with
                user_input: The user's question or input
                chat_history: Previous conversation history
                stream_wait_time: Time to wait between stream chunks
                stream_timeout: Maximum time to wait for response
            
            Returns:
                The streamed response from the VAC
            """
            if chat_history is None:
                chat_history = []
            
            log.info(f"MCP streaming request for VAC '{vector_name}': {user_input}")
            
            try:
                # Collect streaming responses
                full_response = ""
                
                # Check if stream_interpreter is async
                if asyncio.iscoroutinefunction(self.stream_interpreter):
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
                else:
                    # Fall back to sync version for non-async interpreters
                    result = self.stream_interpreter(
                        question=user_input,
                        vector_name=vector_name,
                        chat_history=chat_history
                    )
                    if isinstance(result, dict):
                        full_response = result.get("answer", str(result))
                    else:
                        full_response = str(result)
                
                return full_response or "No response generated"
                
            except Exception as e:
                log.error(f"Error in MCP VAC stream: {str(e)}")
                return f"Error: {str(e)}"
        
        # Register non-streaming tool if interpreter is provided
        if self.vac_interpreter:
            @self.server.tool
            async def vac_query(
                vector_name: str,
                user_input: str,
                chat_history: List[Dict[str, str]] = None
            ) -> str:
                """
                Query a Sunholo VAC (non-streaming).
                
                Args:
                    vector_name: Name of the VAC to interact with
                    user_input: The user's question or input
                    chat_history: Previous conversation history
                
                Returns:
                    The response from the VAC
                """
                if chat_history is None:
                    chat_history = []
                
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
                    
                    return answer
                    
                except Exception as e:
                    log.error(f"Error in MCP VAC query: {str(e)}")
                    return f"Error: {str(e)}"
    
    def get_server(self) -> FastMCP:
        """Get the underlying FastMCP server instance."""
        return self.server
    
    def run(self, transport: str = "stdio", **kwargs):
        """
        Run the MCP server.
        
        Args:
            transport: Transport type ("stdio" or "http")
            **kwargs: Additional arguments for the transport
        """
        self.server.run(transport=transport, **kwargs)
    
    async def run_async(self, transport: str = "stdio", **kwargs):
        """
        Run the MCP server asynchronously.
        
        Args:
            transport: Transport type ("stdio" or "http")
            **kwargs: Additional arguments for the transport
        """
        await self.server.run_async(transport=transport, **kwargs)