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
Built-in VAC tools for MCP server integration.
Provides core Sunholo VAC functionality as MCP tools.
"""

import asyncio
import os
import sys
from typing import Dict, List, Optional, Any

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FastMCP = None
    FASTMCP_AVAILABLE = False

from ..custom_logging import log

# Import with fallbacks for optional dependencies
try:
    from ..utils import ConfigManager
    CONFIG_AVAILABLE = True
except ImportError:
    ConfigManager = None
    CONFIG_AVAILABLE = False

try:
    from ..streaming import start_streaming_chat_async
    STREAMING_AVAILABLE = True
except ImportError:
    start_streaming_chat_async = None
    STREAMING_AVAILABLE = False


def get_vac_config(vector_name: str = None) -> 'ConfigManager':
    """Get VAC configuration for the specified vector name."""
    if not CONFIG_AVAILABLE:
        raise ImportError("ConfigManager not available. Install sunholo with appropriate extras.")
        
    default_vac = os.getenv("DEFAULT_VAC_NAME", "demo")
    vac_name = vector_name or default_vac
    vac_config_folder = os.getenv("VAC_CONFIG_FOLDER")
    
    if vac_config_folder:
        return ConfigManager(vac_name, config_folder=vac_config_folder)
    else:
        return ConfigManager(vac_name)


async def call_vac_async(question: str, vector_name: str, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Call VAC asynchronously using the streaming interface.
    
    Args:
        question: The user's question
        vector_name: Name of the VAC to query
        chat_history: Previous conversation history
        
    Returns:
        The VAC's response
    """
    if not STREAMING_AVAILABLE:
        raise ImportError("Streaming functionality not available. Install sunholo with streaming support.")
        
    if chat_history is None:
        chat_history = []
    
    try:
        config = get_vac_config(vector_name)
        
        # Import the appropriate QNA function based on configuration
        llm_str = config.vacConfig('llm')
        
        if llm_str and 'anthropic' in llm_str.lower():
            try:
                from ..agents.langchain.vertex_genai2 import qna_async
            except ImportError:
                log.warning("Anthropic integration not available, falling back to default")
                from ..agents.langchain.vertex_genai2 import qna_async
        elif llm_str and 'openai' in llm_str.lower():
            try:
                from ..agents.langchain.vertex_genai2 import qna_async
            except ImportError:
                log.warning("OpenAI integration not available, falling back to default")
                from ..agents.langchain.vertex_genai2 import qna_async
        else:
            # Default to vertex AI
            from ..agents.langchain.vertex_genai2 import qna_async
        
        # Use streaming interface to get response
        full_response = ""
        async for chunk in start_streaming_chat_async(
            question=question,
            vector_name=vector_name,
            qna_func_async=qna_async,
            chat_history=chat_history
        ):
            if isinstance(chunk, dict) and 'answer' in chunk:
                full_response = chunk['answer']
            elif isinstance(chunk, str):
                full_response += chunk
        
        return full_response or "No response generated"
        
    except Exception as e:
        log.error(f"Error calling VAC {vector_name}: {str(e)}")
        return f"Error: {str(e)}"


def register_vac_tools(server: 'FastMCP', registry: 'MCPToolRegistry' = None):
    """
    Register built-in VAC tools with a FastMCP server.
    
    Args:
        server: FastMCP server instance
        registry: Optional registry to track tools
    """
    
    @server.tool
    async def vac_stream(
        vector_name: str,
        user_input: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        stream_wait_time: float = 7,
        stream_timeout: float = 120
    ) -> str:
        """
        Stream responses from a Sunholo VAC (Virtual Agent Computer).
        
        Args:
            vector_name: Name of the VAC to interact with
            user_input: The user's question or input  
            chat_history: Previous conversation history
            stream_wait_time: Time to wait between stream chunks (default: 7) 
            stream_timeout: Maximum time to wait for response (default: 120)
        
        Returns:
            The streamed response from the VAC
        """
        if chat_history is None:
            chat_history = []
        
        log.info(f"MCP streaming request for VAC '{vector_name}': {user_input}")
        
        try:
            return await call_vac_async(user_input, vector_name, chat_history)
        except Exception as e:
            log.error(f"Error in MCP VAC stream: {str(e)}")
            return f"Error: {str(e)}"

    @server.tool  
    async def vac_query(
        vector_name: str,
        user_input: str,
        chat_history: Optional[List[Dict[str, str]]] = None
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
            return await call_vac_async(user_input, vector_name, chat_history)
        except Exception as e:
            log.error(f"Error in MCP VAC query: {str(e)}")
            return f"Error: {str(e)}"

    @server.tool
    def list_available_vacs() -> List[str]:
        """
        List all available VAC configurations.
        
        Returns:
            List of available VAC names
        """
        try:
            config = get_vac_config()
            # Try to get available VACs from config
            all_configs = config.load_all_configs()
            if 'vacConfig' in all_configs and 'vac' in all_configs['vacConfig']:
                return list(all_configs['vacConfig']['vac'].keys())
            else:
                return [os.getenv("DEFAULT_VAC_NAME", "demo")]
        except Exception as e:
            log.error(f"Error listing VACs: {str(e)}")
            return [os.getenv("DEFAULT_VAC_NAME", "demo")]

    @server.tool
    def get_vac_info(vector_name: str) -> Dict[str, Any]:
        """
        Get information about a specific VAC configuration.
        
        Args:
            vector_name: Name of the VAC to get info for
            
        Returns:
            Dictionary containing VAC configuration details
        """
        try:
            config = get_vac_config(vector_name)
            return {
                "name": vector_name,
                "llm": config.vacConfig('llm'),
                "model": config.vacConfig('model'), 
                "description": f"VAC configuration for {vector_name}",
                "available": True
            }
        except Exception as e:
            log.error(f"Error getting VAC info for {vector_name}: {str(e)}")
            return {
                "name": vector_name,
                "error": str(e),
                "available": False
            }
    
    # Register tools in registry if provided
    if registry:
        # Extract the underlying function from FunctionTool objects
        registry.register_tool("vac_stream", vac_stream.fn if hasattr(vac_stream, 'fn') else vac_stream)
        registry.register_tool("vac_query", vac_query.fn if hasattr(vac_query, 'fn') else vac_query) 
        registry.register_tool("list_available_vacs", list_available_vacs.fn if hasattr(list_available_vacs, 'fn') else list_available_vacs)
        registry.register_tool("get_vac_info", get_vac_info.fn if hasattr(get_vac_info, 'fn') else get_vac_info)
    
    log.info("Registered built-in VAC tools with MCP server")