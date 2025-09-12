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
import traceback
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

def get_vac_config(vector_name: str = None) -> 'ConfigManager':
    """Get VAC configuration for the specified vector name."""
    if not CONFIG_AVAILABLE:
        raise ImportError("ConfigManager not available. Install sunholo with appropriate extras.")
        
    default_vac = os.getenv("DEFAULT_VAC_NAME", "demo")
    vac_name = vector_name or default_vac
    
    # ConfigManager uses VAC_CONFIG_FOLDER env var automatically
    return ConfigManager(vac_name)


def register_vac_tools(server: 'FastMCP', registry: Optional[Any] = None, *, stream_interpreter: Optional[Any] = None):
    """
    Register built-in VAC tools with a FastMCP server.
    
    Args:
        server: FastMCP server instance
        registry: Optional registry to track tools
        stream_interpreter: The stream interpreter function from VACRoutesFastAPI
    """
    
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
            # If we have a stream_interpreter, use it directly
            if stream_interpreter:
                # Create a no-op callback for non-streaming
                class NoOpCallback:
                    async def async_on_llm_new_token(self, token): pass
                    async def async_on_llm_end(self, response): pass
                    def on_llm_new_token(self, token): pass
                    def on_llm_end(self, response): pass
                
                callback = NoOpCallback()
                
                # Call the stream interpreter
                import inspect
                if inspect.iscoroutinefunction(stream_interpreter):
                    result = await stream_interpreter(
                        question=user_input,
                        vector_name=vector_name,
                        chat_history=chat_history,
                        callback=callback
                    )
                else:
                    # Run sync function in executor
                    import asyncio
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        stream_interpreter,
                        user_input,
                        vector_name,
                        chat_history,
                        callback
                    )
                
                # Extract answer from result
                if isinstance(result, dict):
                    return result.get('answer', str(result))
                else:
                    return str(result)
            else:
                # Fallback to simple response if no interpreter provided
                return f"VAC '{vector_name}' received: {user_input}"
                
        except Exception as e:
            log.error(f"Error in MCP VAC query: {str(e)}")
            log.error(f"Traceback: {traceback.format_exc()}")
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
        registry.register_tool("vac_query", vac_query.fn if hasattr(vac_query, 'fn') else vac_query) 
        registry.register_tool("list_available_vacs", list_available_vacs.fn if hasattr(list_available_vacs, 'fn') else list_available_vacs)
        registry.register_tool("get_vac_info", get_vac_info.fn if hasattr(get_vac_info, 'fn') else get_vac_info)
    
    log.info("Registered built-in VAC tools with MCP server")