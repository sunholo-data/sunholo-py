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

from __future__ import annotations

import json
import traceback
import datetime
import uuid
import inspect
import asyncio
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from functools import partial
from contextlib import asynccontextmanager

if TYPE_CHECKING:
    from fastapi import FastAPI, Request, Response, HTTPException
    from fastapi.responses import StreamingResponse, JSONResponse
    from pydantic import BaseModel

try:
    from fastapi import FastAPI, Request, Response, HTTPException
    from fastapi.responses import StreamingResponse, JSONResponse
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FastAPI = None
    Request = None
    Response = None
    HTTPException = None
    StreamingResponse = None
    JSONResponse = None
    BaseModel = object
    FASTAPI_AVAILABLE = False

from ..chat_history import extract_chat_history_with_cache, extract_chat_history_async_cached
from ...qna.parsers import parse_output
from ...streaming import start_streaming_chat, start_streaming_chat_async
from ...archive import archive_qa
from ...custom_logging import log
from ...utils import ConfigManager
from ...utils.version import sunholo_version

try:
    from ...mcp.mcp_manager import MCPClientManager
except ImportError:
    MCPClientManager = None

try:
    from ...mcp.vac_mcp_server_fastmcp import VACMCPServer
except ImportError:
    VACMCPServer = None

try:
    from ...a2a.vac_a2a_agent import VACA2AAgent
except (ImportError, SyntaxError):
    VACA2AAgent = None


class VACRequest(BaseModel):
    """Request model for VAC endpoints."""
    user_input: str
    chat_history: Optional[List] = None
    stream_wait_time: Optional[int] = 7
    stream_timeout: Optional[int] = 120
    vector_name: Optional[str] = None
    trace_id: Optional[str] = None
    eval_percent: Optional[float] = 0.01


class VACRoutesFastAPI:
    """
    FastAPI implementation of VAC routes with streaming support and extensible MCP integration.
    
    This class provides a comprehensive FastAPI application with:
    - VAC (Virtual Agent Computer) endpoints for AI chat and streaming
    - OpenAI-compatible API endpoints
    - Extensible MCP (Model Context Protocol) server integration for Claude Desktop/Code
    - MCP client support for connecting to external MCP servers
    - A2A (Agent-to-Agent) protocol support
    - Server-Sent Events (SSE) streaming capabilities
    
    ## Key Features
    
    ### 1. VAC Endpoints
    - `/vac/{vector_name}` - Non-streaming VAC responses
    - `/vac/streaming/{vector_name}` - Plain text streaming responses
    - `/vac/streaming/{vector_name}/sse` - Server-Sent Events streaming
    
    ### 2. OpenAI Compatible API
    - `/openai/v1/chat/completions` - OpenAI-compatible chat completions
    - Supports both streaming and non-streaming modes
    
    ### 3. MCP Integration
    - **MCP Server**: Expose your VAC as MCP tools for Claude Desktop/Code
    - **MCP Client**: Connect to external MCP servers and use their tools
    - **Custom Tools**: Easily add your own MCP tools using decorators
    
    ### 4. A2A Agent Protocol
    - Agent discovery and task execution
    - Compatible with multi-agent workflows
    
    ## Basic Usage
    
    ### Simplified Setup (Recommended)
    
    Use the helper method for automatic lifespan management:
    
    ```python
    from sunholo.agents.fastapi import VACRoutesFastAPI
    
    async def my_stream_interpreter(question, vector_name, chat_history, callback, **kwargs):
        # Your streaming VAC logic here
        # Use callback.async_on_llm_new_token(token) for streaming
        return {"answer": "Response", "sources": []}
    
    # Single call sets up everything with MCP server and proper lifespan management
    app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
        title="My VAC Application",
        stream_interpreter=my_stream_interpreter
        # MCP server is automatically enabled when using this method
    )
    
    # Add custom endpoints if needed
    @app.get("/custom")
    async def custom_endpoint():
        return {"message": "Hello"}
    
    # Run the app
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    ```
    
    ### Manual Setup (Advanced)
    
    For more control over lifespan management:
    
    ```python
    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from sunholo.agents.fastapi import VACRoutesFastAPI
    
    async def my_stream_interpreter(question, vector_name, chat_history, callback, **kwargs):
        return {"answer": "Response", "sources": []}
    
    # Define your app's lifespan
    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        print("Starting up...")
        yield
        print("Shutting down...")
    
    # Create temp app to get MCP lifespan
    temp_app = FastAPI()
    vac_routes_temp = VACRoutesFastAPI(
        temp_app,
        stream_interpreter=my_stream_interpreter,
        enable_mcp_server=True
    )
    
    # Get MCP lifespan
    mcp_lifespan = vac_routes_temp.get_mcp_lifespan()
    
    # Combine lifespans
    @asynccontextmanager
    async def combined_lifespan(app: FastAPI):
        async with app_lifespan(app):
            if mcp_lifespan:
                async with mcp_lifespan(app):
                    yield
            else:
                yield
    
    # Create app with combined lifespan
    app = FastAPI(title="My VAC Application", lifespan=combined_lifespan)
    
    # Initialize VAC routes
    vac_routes = VACRoutesFastAPI(
        app=app,
        stream_interpreter=my_stream_interpreter,
        enable_mcp_server=True
    )
    ```
    
    Your FastAPI app now includes:
    - All VAC endpoints  
    - MCP server at /mcp (for Claude Desktop/Code to connect)
    - Built-in VAC tools: vac_stream, vac_query, list_available_vacs, get_vac_info
    
    ## Adding Custom MCP Tools
    
    ### Method 1: Using Decorators
    ```python
    vac_routes = VACRoutesFastAPI(app, stream_interpreter, enable_mcp_server=True)
    
    @vac_routes.add_mcp_tool
    async def get_weather(city: str) -> str:
        '''Get weather information for a city.'''
        # Your weather API logic
        return f"Weather in {city}: Sunny, 22°C"
    
    @vac_routes.add_mcp_tool("custom_search", "Search our database")
    async def search_database(query: str, limit: int = 10) -> list:
        '''Search internal database with custom name and description.'''
        # Your database search logic
        return [{"result": f"Found: {query}"}]
    ```
    
    ### Method 2: Programmatic Registration
    ```python
    async def my_business_tool(param: str) -> dict:
        return {"processed": param}
    
    # Add tool with custom name and description
    vac_routes.add_mcp_tool(
        my_business_tool, 
        "process_business_data", 
        "Process business data with our custom logic"
    )
    ```
    
    ### Method 3: Advanced MCP Server Access
    ```python
    # Get direct access to MCP server for advanced customization
    mcp_server = vac_routes.get_mcp_server()
    
    @mcp_server.add_tool
    async def advanced_tool(complex_param: dict) -> str:
        return f"Advanced processing: {complex_param}"
    
    # List all registered tools
    print("Available MCP tools:", vac_routes.list_mcp_tools())
    ```
    
    ## MCP Client Integration
    
    Connect to external MCP servers and use their tools:
    
    ```python
    mcp_servers = [
        {
            "name": "filesystem-server",
            "command": "npx",
            "args": ["@modelcontextprotocol/server-filesystem", "/path/to/files"]
        }
    ]
    
    vac_routes = VACRoutesFastAPI(
        app, stream_interpreter,
        mcp_servers=mcp_servers,  # Connect to external MCP servers
        enable_mcp_server=True    # Also expose our own MCP server
    )
    
    # External MCP tools available at:
    # GET /mcp/tools - List all external tools
    # POST /mcp/call - Call external MCP tools
    ```
    
    ## Claude Desktop Integration
    
    ### Option 1: Remote Integration (Recommended for Development)
    ```python
    # Run your FastAPI app
    uvicorn.run(vac_routes.app, host="0.0.0.0", port=8000)
    
    # Configure Claude Desktop (Settings > Connectors > Add custom connector):
    # URL: http://localhost:8000/mcp
    ```
    
    ### Option 2: Local Integration
    Create a standalone script for Claude Desktop:
    ```python
    # claude_mcp_server.py
    from sunholo.mcp.extensible_mcp_server import create_mcp_server
    
    server = create_mcp_server("my-app", include_vac_tools=True)
    
    @server.add_tool
    async def my_app_tool(param: str) -> str:
        return f"My app processed: {param}"
    
    if __name__ == "__main__":
        server.run()
    
    # Install: fastmcp install claude-desktop claude_mcp_server.py --with sunholo[anthropic]
    ```
    
    ## Available Built-in MCP Tools
    
    When `enable_mcp_server=True`, these tools are automatically available:
    
    - **`vac_stream`**: Stream responses from any configured VAC
    - **`vac_query`**: Query VACs with non-streaming responses
    - **`list_available_vacs`**: List all available VAC configurations
    - **`get_vac_info`**: Get detailed information about a specific VAC
    
    ## Error Handling and Best Practices
    
    ```python
    @vac_routes.add_mcp_tool
    async def robust_tool(user_input: str) -> str:
        '''Example of robust tool implementation.'''
        try:
            # Validate input
            if not user_input or len(user_input) > 1000:
                return "Error: Invalid input length"
            
            # Your business logic
            result = await process_user_input(user_input)
            
            return f"Processed: {result}"
            
        except Exception as e:
            # Log error and return user-friendly message
            log.error(f"Tool error: {e}")
            return f"Error processing request: {str(e)}"
    ```
    
    ## Configuration Options
    
    ```python
    vac_routes = VACRoutesFastAPI(
        app=app,
        stream_interpreter=my_stream_func,
        vac_interpreter=my_vac_func,           # Optional non-streaming function
        additional_routes=[],                   # Custom FastAPI routes
        mcp_servers=[],                        # External MCP servers to connect to
        add_langfuse_eval=True,                # Enable Langfuse evaluation
        enable_mcp_server=True,                # Enable MCP server for Claude
        enable_a2a_agent=False,                # Enable A2A agent protocol
        a2a_vac_names=None                     # VACs available for A2A
    )
    ```
    """
    
    def __init__(
        self,
        app: FastAPI,
        stream_interpreter: Callable,
        vac_interpreter: Optional[Callable] = None,
        additional_routes: Optional[List[Dict]] = None,
        mcp_servers: Optional[List[Dict[str, Any]]] = None,
        add_langfuse_eval: bool = True,
        enable_a2a_agent: bool = False,
        a2a_vac_names: Optional[List[str]] = None
    ):
        """
        Initialize FastAPI VAC routes with comprehensive AI and MCP integration.
        
        Args:
            app: FastAPI application instance to register routes on
            stream_interpreter: Function for streaming VAC responses. Can be async or sync.
                               Called with (question, vector_name, chat_history, callback, **kwargs)
            vac_interpreter: Optional function for non-streaming VAC responses. If not provided,
                           will use stream_interpreter without streaming callbacks.
            additional_routes: List of custom route dictionaries to register:
                             [{"path": "/custom", "handler": func, "methods": ["GET"]}]
            mcp_servers: List of external MCP server configurations to connect to:
                       [{"name": "server-name", "command": "python", "args": ["server.py"]}]
            add_langfuse_eval: Whether to enable Langfuse evaluation and tracing
            enable_a2a_agent: Whether to enable A2A (Agent-to-Agent) protocol endpoints
            a2a_vac_names: List of VAC names available for A2A agent interactions
        
        ## Stream Interpreter Function
        
        Your stream_interpreter should handle streaming responses:
        
        ```python
        async def my_stream_interpreter(question: str, vector_name: str, 
                                      chat_history: list, callback, **kwargs):
            # Process the question using your AI/RAG pipeline
            
            # For streaming tokens:
            await callback.async_on_llm_new_token("partial response...")
            
            # Return final result with sources:
            return {
                "answer": "Final complete answer",
                "sources": [{"title": "Source 1", "url": "..."}]
            }
        ```
        
        ## MCP Server Integration
        
        When VACMCPServer is available, the following happens automatically:
        1. MCP server is mounted at /mcp endpoint
        2. Built-in VAC tools are automatically registered:
           - vac_stream, vac_query, list_available_vacs, get_vac_info
        3. You can add custom MCP tools using add_mcp_tool()
        4. Claude Desktop/Code can connect to http://your-server/mcp
        
        ## Complete Example
        
        ```python
        app = FastAPI(title="My VAC Application")
        
        async def my_vac_logic(question, vector_name, chat_history, callback, **kwargs):
            # Your AI/RAG implementation
            result = await process_with_ai(question)
            return {"answer": result, "sources": []}
        
        # External MCP servers to connect to
        external_mcp = [
            {"name": "filesystem", "command": "mcp-server-fs", "args": ["/data"]}
        ]
        
        vac_routes = VACRoutesFastAPI(
            app=app,
            stream_interpreter=my_vac_logic,
            mcp_servers=external_mcp,
            enable_mcp_server=True  # Enable for Claude integration
        )
        
        # Add custom MCP tools for your business logic
        @vac_routes.add_mcp_tool
        async def get_customer_info(customer_id: str) -> dict:
            return await fetch_customer(customer_id)
        
        # Your app now has:
        # - VAC endpoints: /vac/{vector_name}, /vac/streaming/{vector_name}
        # - OpenAI API: /openai/v1/chat/completions
        # - MCP server: /mcp (with built-in + custom tools)
        # - MCP client: /mcp/tools, /mcp/call (for external servers)
        ```
        """
        self.app = app
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter or partial(self.vac_interpreter_default)
        
        # Detect if interpreters are async
        self.stream_is_async = inspect.iscoroutinefunction(stream_interpreter)
        self.vac_is_async = inspect.iscoroutinefunction(self.vac_interpreter)
        
        # MCP client initialization
        self.mcp_servers = mcp_servers or []
        self.mcp_client_manager = MCPClientManager() if MCPClientManager else None
        self._mcp_initialized = False
        
        # MCP server initialization - automatically enabled if VACMCPServer is available
        self.vac_mcp_server = None
        self._custom_mcp_tools = []
        self._custom_mcp_resources = []
        
        # Enable MCP server if VACMCPServer is available
        if VACMCPServer:
            self.vac_mcp_server = VACMCPServer(
                server_name="sunholo-vac-fastapi-server",
                include_vac_tools=True
            )
            
            # Add any pre-registered custom tools
            self._register_custom_tools()
        
        # A2A agent initialization
        self.enable_a2a_agent = enable_a2a_agent
        self.vac_a2a_agent = None
        self.a2a_vac_names = a2a_vac_names
        
        self.additional_routes = additional_routes or []
        self.add_langfuse_eval = add_langfuse_eval
        
        self.register_routes()
    
    @staticmethod
    def create_app_with_mcp(
        title: str = "VAC Application",
        stream_interpreter: Optional[callable] = None,
        vac_interpreter: Optional[callable] = None,
        app_lifespan: Optional[callable] = None,
        **kwargs
    ) -> tuple[FastAPI, 'VACRoutesFastAPI']:
        """
        Helper method to create a FastAPI app with proper MCP lifespan management.
        
        This method simplifies the setup process by handling the lifespan combination
        automatically, avoiding the need for the double initialization pattern.
        MCP server is automatically enabled when using this method.
        
        Args:
            title: Title for the FastAPI app
            stream_interpreter: Streaming interpreter function
            vac_interpreter: Non-streaming interpreter function  
            app_lifespan: Optional app lifespan context manager
            **kwargs: Additional arguments passed to VACRoutesFastAPI
            
        Returns:
            Tuple of (FastAPI app, VACRoutesFastAPI instance)
            
        Example:
            ```python
            from sunholo.agents.fastapi import VACRoutesFastAPI
            
            async def my_interpreter(question, vector_name, chat_history, callback, **kwargs):
                # Your logic here
                return {"answer": "response", "sources": []}
            
            # Single call to set up everything (MCP is automatically enabled)
            app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
                title="My VAC App",
                stream_interpreter=my_interpreter
            )
            
            # Add custom endpoints
            @app.get("/custom")
            async def custom_endpoint():
                return {"message": "Custom endpoint"}
            
            if __name__ == "__main__":
                import uvicorn
                uvicorn.run(app, host="0.0.0.0", port=8000)
            ```
        """
        from contextlib import asynccontextmanager
        
        # Default app lifespan if not provided
        if app_lifespan is None:
            @asynccontextmanager
            async def app_lifespan(app: FastAPI):
                yield
        
        # Import here to avoid circular imports
        if VACMCPServer:
            from fastmcp import FastMCP
            
            # Create MCP server directly to get its lifespan
            mcp_server = FastMCP("sunholo-vac-fastapi-server")
            
            # Register built-in VAC tools directly with the stream interpreter
            from sunholo.mcp.vac_tools import register_vac_tools
            register_vac_tools(mcp_server, registry=None, stream_interpreter=stream_interpreter)
            
            # Get the MCP app with path="" so when mounted at /mcp it's accessible at /mcp
            mcp_app = mcp_server.http_app(path="", stateless_http=True)
            
            # Create combined lifespan
            @asynccontextmanager  
            async def combined_lifespan(app: FastAPI):
                async with app_lifespan(app):
                    async with mcp_app.lifespan(app):
                        yield
            
            # Create the actual app with combined lifespan
            app = FastAPI(
                title=title,
                lifespan=combined_lifespan
            )
            
            # Mount the MCP app at /mcp
            app.mount("/mcp", mcp_app)
            
            # Now create VAC routes WITHOUT MCP (since we already mounted it)
            vac_routes = VACRoutesFastAPI(
                app,
                stream_interpreter=stream_interpreter,
                vac_interpreter=vac_interpreter,
                **kwargs
            )
            
            # Store reference to MCP server for tool registration
            vac_routes.vac_mcp_server = type('MockMCPServer', (), {
                'add_tool': lambda self, func, name=None, desc=None: mcp_server.tool(func) if name is None else mcp_server.tool(name=name)(func),
                'server': mcp_server
            })()
        else:
            # No MCP support available
            app = FastAPI(
                title=title,
                lifespan=app_lifespan
            )
            
            vac_routes = VACRoutesFastAPI(
                app,
                stream_interpreter=stream_interpreter,
                vac_interpreter=vac_interpreter,
                **kwargs
            )
        
        return app, vac_routes
    
    def get_mcp_lifespan(self):
        """
        Get the MCP app's lifespan for manual lifespan management.
        
        Returns:
            The MCP app's lifespan if MCP server is enabled, None otherwise.
            
        Example:
            ```python
            from contextlib import asynccontextmanager
            
            # Create temp app to get MCP lifespan
            temp_app = FastAPI()
            vac_routes = VACRoutesFastAPI(temp_app, ..., enable_mcp_server=True)
            mcp_lifespan = vac_routes.get_mcp_lifespan()
            
            # Combine with your app's lifespan
            @asynccontextmanager
            async def combined_lifespan(app: FastAPI):
                async with my_app_lifespan(app):
                    if mcp_lifespan:
                        async with mcp_lifespan(app):
                            yield
                    else:
                        yield
            
            app = FastAPI(lifespan=combined_lifespan)
            ```
        """
        if self.vac_mcp_server:
            mcp_app = self.vac_mcp_server.get_http_app()
            return mcp_app.lifespan
        return None
    
    async def vac_interpreter_default(self, question: str, vector_name: str, chat_history=None, **kwargs):
        """Default VAC interpreter that uses the stream interpreter without streaming."""
        class NoOpCallback:
            def on_llm_new_token(self, token):
                pass
            def on_llm_end(self, response):
                pass
            async def async_on_llm_new_token(self, token):
                pass
            async def async_on_llm_end(self, response):
                pass
        
        callback = NoOpCallback()
        
        if self.stream_is_async:
            result = await self.stream_interpreter(
                question=question,
                vector_name=vector_name,
                chat_history=chat_history or [],
                callback=callback,
                **kwargs
            )
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.stream_interpreter,
                question,
                vector_name,
                chat_history or [],
                callback,
                **kwargs
            )
        
        return result
    
    def register_routes(self):
        """Register all VAC routes with the FastAPI application."""
        # Basic routes
        self.app.get("/")(self.home)
        self.app.get("/health")(self.health)
        
        # Streaming endpoints - both SSE and plain text
        self.app.post("/vac/streaming/{vector_name}")(self.handle_stream_vac)
        self.app.post("/vac/streaming/{vector_name}/sse")(self.handle_stream_vac_sse)
        
        # Static VAC endpoint
        self.app.post("/vac/{vector_name}")(self.handle_process_vac)
        
        # OpenAI compatible endpoints
        self.app.get("/openai/health")(self.openai_health)
        self.app.post("/openai/health")(self.openai_health)
        self.app.post("/openai/v1/chat/completions")(self.handle_openai_compatible)
        self.app.post("/openai/v1/chat/completions/{vector_name}")(self.handle_openai_compatible)
        
        # MCP client routes
        if self.mcp_servers and self.mcp_client_manager:
            self.app.get("/mcp/tools")(self.handle_mcp_list_tools)
            self.app.get("/mcp/tools/{server_name}")(self.handle_mcp_list_tools)
            self.app.post("/mcp/call")(self.handle_mcp_call_tool)
            self.app.get("/mcp/resources")(self.handle_mcp_list_resources)
            self.app.post("/mcp/resources/read")(self.handle_mcp_read_resource)
        
        # MCP server endpoint - mount the FastMCP app
        if self.vac_mcp_server:
            try:
                mcp_app = self.vac_mcp_server.get_http_app()
                
                # Note: FastAPI doesn't expose lifespan as a public attribute,
                # so we can't easily check if it's configured. The error will be
                # caught below if lifespan is missing.
                
                # Mount at root - the MCP app already has /mcp path configured
                self.app.mount("", mcp_app)
                log.info("✅ MCP server mounted at /mcp endpoint")
                
            except RuntimeError as e:
                if "Task group is not initialized" in str(e):
                    error_msg = (
                        "MCP server initialization failed: Lifespan not configured properly.\n"
                        "The FastAPI app must be created with the MCP lifespan.\n\n"
                        "Quick fix: Use the helper method:\n"
                        "  app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(\n"
                        "      stream_interpreter=your_interpreter\n"
                        "  )\n\n"
                        "Or manually configure the lifespan - see documentation for details."
                    )
                    log.error(error_msg)
                    raise RuntimeError(error_msg) from e
                else:
                    log.error(f"Failed to mount MCP server: {e}")
                    raise RuntimeError(f"MCP server initialization failed: {e}") from e
            except Exception as e:
                log.error(f"Failed to mount MCP server: {e}")
                raise RuntimeError(f"MCP server initialization failed: {e}") from e
        
        # MCP debug endpoint - add if we have a MCP server instance
        if self.vac_mcp_server:
            self.app.get("/debug/mcp")(self.handle_mcp_debug)
        
        # A2A agent endpoints
        if self.enable_a2a_agent:
            self.app.get("/.well-known/agent.json")(self.handle_a2a_agent_card)
            self.app.post("/a2a/tasks/send")(self.handle_a2a_task_send)
            self.app.post("/a2a/tasks/sendSubscribe")(self.handle_a2a_task_send_subscribe)
            self.app.post("/a2a/tasks/get")(self.handle_a2a_task_get)
            self.app.post("/a2a/tasks/cancel")(self.handle_a2a_task_cancel)
            self.app.post("/a2a/tasks/pushNotification/set")(self.handle_a2a_push_notification)
        
        # Register additional custom routes
        for route in self.additional_routes:
            self.app.add_api_route(
                route["path"],
                route["handler"],
                methods=route.get("methods", ["GET"])
            )
        
        # Set up lifespan for MCP initialization
        self._setup_lifespan()
    
    def _setup_lifespan(self):
        """Set up lifespan context manager for app initialization."""
        # Only set lifespan if we have MCP servers to initialize
        if not (self.mcp_servers and self.mcp_client_manager):
            return
        
        # Store the existing lifespan if any
        existing_lifespan = getattr(self.app, 'router', self.app).lifespan_context
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            if not self._mcp_initialized:
                await self._initialize_mcp_servers()
                self._mcp_initialized = True
            
            # Call existing lifespan startup if any
            if existing_lifespan:
                async with existing_lifespan(app) as lifespan_state:
                    yield lifespan_state
            else:
                yield
            
            # Shutdown (no cleanup needed for now)
        
        # Set the new lifespan
        self.app.router.lifespan_context = lifespan
    
    async def home(self):
        """Home endpoint."""
        return JSONResponse(content="OK")
    
    async def health(self):
        """Health check endpoint."""
        return JSONResponse(content={"status": "healthy"})
    
    async def handle_stream_vac(self, vector_name: str, request: Request):
        """
        Handle streaming VAC requests with plain text response.
        Compatible with Flask implementation.
        """
        data = await request.json()
        vac_request = VACRequest(**data)
        
        prep = await self.prep_vac_async(vac_request, vector_name)
        all_input = prep["all_input"]
        
        log.info(f'Streaming data with: {all_input}')
        
        async def generate_response():
            try:
                if self.stream_is_async:
                    # Use async streaming
                    async for chunk in start_streaming_chat_async(
                        question=all_input["user_input"],
                        vector_name=vector_name,
                        qna_func_async=self.stream_interpreter,
                        chat_history=all_input["chat_history"],
                        wait_time=all_input["stream_wait_time"],
                        timeout=all_input["stream_timeout"],
                        **all_input["kwargs"]
                    ):
                        if isinstance(chunk, dict) and 'answer' in chunk:
                            archive_qa(chunk, vector_name)  # This is a sync function, not async
                            yield json.dumps(chunk)
                        else:
                            yield chunk
                else:
                    # Run sync streaming in executor
                    loop = asyncio.get_event_loop()
                    
                    # Create a queue for passing chunks from sync to async
                    queue = asyncio.Queue()
                    
                    def run_sync_streaming():
                        for chunk in start_streaming_chat(
                            question=all_input["user_input"],
                            vector_name=vector_name,
                            qna_func=self.stream_interpreter,
                            chat_history=all_input["chat_history"],
                            wait_time=all_input["stream_wait_time"],
                            timeout=all_input["stream_timeout"],
                            **all_input["kwargs"]
                        ):
                            asyncio.run_coroutine_threadsafe(queue.put(chunk), loop)
                        asyncio.run_coroutine_threadsafe(queue.put(None), loop)
                    
                    # Run sync function in thread
                    await loop.run_in_executor(None, run_sync_streaming)
                    
                    # Yield from queue
                    while True:
                        chunk = await queue.get()
                        if chunk is None:
                            break
                        if isinstance(chunk, dict) and 'answer' in chunk:
                            archive_qa(chunk, vector_name)  # This is a sync function, not async
                            yield json.dumps(chunk)
                        else:
                            yield chunk
                            
            except Exception as e:
                yield f"Streaming Error: {str(e)} {traceback.format_exc()}"
        
        return StreamingResponse(
            generate_response(),
            media_type='text/plain; charset=utf-8',
            headers={
                'Transfer-Encoding': 'chunked',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )
    
    async def handle_stream_vac_sse(self, vector_name: str, request: Request):
        """
        Handle streaming VAC requests with Server-Sent Events format.
        Better for browser-based clients.
        """
        data = await request.json()
        vac_request = VACRequest(**data)
        
        prep = await self.prep_vac_async(vac_request, vector_name)
        all_input = prep["all_input"]
        
        log.info(f'SSE Streaming data with: {all_input}')
        
        async def generate_sse():
            try:
                if self.stream_is_async:
                    log.info(f"Starting async streaming for {vector_name}")
                    async for chunk in start_streaming_chat_async(
                        question=all_input["user_input"],
                        vector_name=vector_name,
                        qna_func_async=self.stream_interpreter,
                        chat_history=all_input["chat_history"],
                        wait_time=all_input["stream_wait_time"],
                        timeout=all_input["stream_timeout"],
                        **all_input["kwargs"]
                    ):
                        log.info(f"Got chunk from start_streaming_chat_async: type={type(chunk)}, is_dict={isinstance(chunk, dict)}, has_answer={'answer' in chunk if isinstance(chunk, dict) else 'N/A'}")
                        if isinstance(chunk, dict) and 'answer' in chunk:
                            # This is the final response with answer and sources
                            log.info(f"Final response received: {list(chunk.keys())}")
                            archive_qa(chunk, vector_name)  # This is a sync function, not async
                            # Send the complete response with sources
                            final_data = f"data: {json.dumps(chunk)}\n\n"
                            log.info(f"Yielding final response: {final_data[:100]}...")
                            yield final_data
                            # Then send the completion signal
                            done_signal = "data: [DONE]\n\n"
                            log.info("Yielding [DONE] signal")
                            yield done_signal
                            log.info("Sent [DONE] signal, breaking loop")
                            break  # Exit after sending final response
                        elif chunk:  # Only send non-empty chunks
                            # This is a streaming text chunk
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    log.info("SSE generator completed")
                else:
                    # Handle sync interpreter - similar to above
                    loop = asyncio.get_event_loop()
                    queue = asyncio.Queue()
                    
                    def run_sync_streaming():
                        for chunk in start_streaming_chat(
                            question=all_input["user_input"],
                            vector_name=vector_name,
                            qna_func=self.stream_interpreter,
                            chat_history=all_input["chat_history"],
                            wait_time=all_input["stream_wait_time"],
                            timeout=all_input["stream_timeout"],
                            **all_input["kwargs"]
                        ):
                            asyncio.run_coroutine_threadsafe(queue.put(chunk), loop)
                        asyncio.run_coroutine_threadsafe(queue.put(None), loop)
                    
                    await loop.run_in_executor(None, run_sync_streaming)
                    
                    while True:
                        chunk = await queue.get()
                        if chunk is None:
                            break
                        if isinstance(chunk, dict) and 'answer' in chunk:
                            # This is the final response with answer and sources
                            archive_qa(chunk, vector_name)  # This is a sync function, not async
                            # Send the complete response with sources
                            yield f"data: {json.dumps(chunk)}\n\n"
                            # Then send the completion signal
                            yield "data: [DONE]\n\n"
                            break  # Exit after sending final response
                        elif chunk:  # Only send non-empty chunks
                            # This is a streaming text chunk
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                            
            except Exception as e:
                import traceback
                log.error(f"Error in SSE generator: {e}\n{traceback.format_exc()}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_sse(),
            media_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    
    async def handle_process_vac(self, vector_name: str, request: Request):
        """Handle non-streaming VAC requests."""
        data = await request.json()
        vac_request = VACRequest(**data)
        
        prep = await self.prep_vac_async(vac_request, vector_name)
        all_input = prep["all_input"]
        
        try:
            if self.vac_is_async:
                bot_output = await self.vac_interpreter(
                    question=all_input["user_input"],
                    vector_name=vector_name,
                    chat_history=all_input["chat_history"],
                    **all_input["kwargs"]
                )
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                bot_output = await loop.run_in_executor(
                    None,
                    self.vac_interpreter,
                    all_input["user_input"],
                    vector_name,
                    all_input["chat_history"],
                    **all_input["kwargs"]
                )
            
            bot_output = parse_output(bot_output)
            archive_qa(bot_output, vector_name)  # This is a sync function, not async
            log.info(f'==LLM Q:{all_input["user_input"]} - A:{bot_output}')
            
        except Exception as err:
            bot_output = {
                'answer': f'QNA_ERROR: An error occurred while processing /vac/{vector_name}: {str(err)} traceback: {traceback.format_exc()}'
            }
        
        return JSONResponse(content=bot_output)
    
    async def prep_vac_async(self, vac_request: VACRequest, vector_name: str):
        """Prepare VAC request data asynchronously."""
        try:
            vac_config = ConfigManager(vector_name)
        except Exception as e:
            raise ValueError(f"Unable to find vac_config for {vector_name} - {str(e)}")
        
        # Extract chat history
        paired_messages = await extract_chat_history_async_cached(vac_request.chat_history)
        
        all_input = {
            'user_input': vac_request.user_input.strip(),
            'vector_name': vac_request.vector_name or vector_name,
            'chat_history': paired_messages,
            'stream_wait_time': vac_request.stream_wait_time,
            'stream_timeout': vac_request.stream_timeout,
            'eval_percent': vac_request.eval_percent,
            'kwargs': {}
        }
        
        return {
            "all_input": all_input,
            "vac_config": vac_config
        }
    
    async def openai_health(self):
        """OpenAI health check endpoint."""
        return JSONResponse(content={'message': 'Success'})
    
    async def handle_openai_compatible(self, request: Request, vector_name: Optional[str] = None):
        """Handle OpenAI-compatible chat completion requests."""
        data = await request.json()
        log.info(f'OpenAI compatible endpoint got data: {data} for vector: {vector_name}')
        
        vector_name = vector_name or data.pop('model', None)
        messages = data.pop('messages', None)
        chat_history = data.pop('chat_history', None)
        stream = data.pop('stream', False)
        
        if not messages:
            return JSONResponse(content={"error": "No messages provided"}, status_code=400)
        
        # Extract user message
        user_message = None
        for msg in reversed(messages):
            if msg['role'] == 'user':
                if isinstance(msg['content'], list):
                    for content_item in msg['content']:
                        if content_item['type'] == 'text':
                            user_message = content_item['text']
                            break
                else:
                    user_message = msg['content']
                break
        
        if not user_message:
            return JSONResponse(content={"error": "No user message provided"}, status_code=400)
        
        response_id = str(uuid.uuid4())
        
        if stream:
            async def generate_openai_stream():
                if self.stream_is_async:
                    async for chunk in start_streaming_chat_async(
                        question=user_message,
                        vector_name=vector_name,
                        qna_func_async=self.stream_interpreter,
                        chat_history=chat_history or [],
                        wait_time=data.get("stream_wait_time", 1),
                        timeout=data.get("stream_timeout", 60),
                        **data
                    ):
                        if isinstance(chunk, dict) and 'answer' in chunk:
                            openai_chunk = {
                                "id": response_id,
                                "object": "chat.completion.chunk",
                                "created": int(datetime.datetime.now().timestamp()),
                                "model": vector_name,
                                "system_fingerprint": sunholo_version(),
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": chunk['answer']},
                                    "logprobs": None,
                                    "finish_reason": None
                                }]
                            }
                            yield f"data: {json.dumps(openai_chunk)}\n\n"
                        else:
                            # Stream partial content
                            openai_chunk = {
                                "id": response_id,
                                "object": "chat.completion.chunk",
                                "created": int(datetime.datetime.now().timestamp()),
                                "model": vector_name,
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": chunk},
                                    "finish_reason": None
                                }]
                            }
                            yield f"data: {json.dumps(openai_chunk)}\n\n"
                
                # Send final chunk
                final_chunk = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": int(datetime.datetime.now().timestamp()),
                    "model": vector_name,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_openai_stream(),
                media_type='text/event-stream'
            )
        else:
            # Non-streaming response
            try:
                if self.vac_is_async:
                    bot_output = await self.vac_interpreter(
                        question=user_message,
                        vector_name=vector_name,
                        chat_history=chat_history or [],
                        **data
                    )
                else:
                    loop = asyncio.get_event_loop()
                    bot_output = await loop.run_in_executor(
                        None,
                        self.vac_interpreter,
                        user_message,
                        vector_name,
                        chat_history or [],
                        **data
                    )
                
                bot_output = parse_output(bot_output)
                answer = bot_output.get('answer', '')
                
                openai_response = {
                    "id": response_id,
                    "object": "chat.completion",
                    "created": int(datetime.datetime.now().timestamp()),
                    "model": vector_name,
                    "system_fingerprint": sunholo_version(),
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": answer,
                        },
                        "logprobs": None,
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(user_message.split()),
                        "completion_tokens": len(answer.split()),
                        "total_tokens": len(user_message.split()) + len(answer.split())
                    }
                }
                
                return JSONResponse(content=openai_response)
                
            except Exception as err:
                log.error(f"OpenAI response error: {str(err)} traceback: {traceback.format_exc()}")
                return JSONResponse(
                    content={"error": f"ERROR: {str(err)}"},
                    status_code=500
                )
    
    async def _initialize_mcp_servers(self):
        """Initialize connections to configured MCP servers."""
        for server_config in self.mcp_servers:
            try:
                await self.mcp_client_manager.connect_to_server(
                    server_name=server_config["name"],
                    command=server_config["command"],
                    args=server_config.get("args", [])
                )
                log.info(f"Connected to MCP server: {server_config['name']}")
            except Exception as e:
                log.error(f"Failed to connect to MCP server {server_config['name']}: {e}")
    
    async def handle_mcp_list_tools(self, server_name: Optional[str] = None):
        """List available MCP tools."""
        if not self.mcp_client_manager:
            raise HTTPException(status_code=501, detail="MCP client not available")
        
        tools = await self.mcp_client_manager.list_tools(server_name)
        return JSONResponse(content={
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                    "server": tool.metadata.get("server") if tool.metadata else server_name
                }
                for tool in tools
            ]
        })
    
    async def handle_mcp_call_tool(self, request: Request):
        """Call an MCP tool."""
        if not self.mcp_client_manager:
            raise HTTPException(status_code=501, detail="MCP client not available")
        
        data = await request.json()
        server_name = data.get("server")
        tool_name = data.get("tool")
        arguments = data.get("arguments", {})
        
        if not server_name or not tool_name:
            raise HTTPException(status_code=400, detail="Missing 'server' or 'tool' parameter")
        
        try:
            result = await self.mcp_client_manager.call_tool(server_name, tool_name, arguments)
            
            # Convert result to JSON-serializable format
            if hasattr(result, 'content'):
                if hasattr(result.content, 'text'):
                    return JSONResponse(content={"result": result.content.text})
                elif hasattr(result.content, 'data'):
                    return JSONResponse(content={"result": result.content.data})
                else:
                    return JSONResponse(content={"result": str(result.content)})
            else:
                return JSONResponse(content={"result": str(result)})
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def handle_mcp_list_resources(self, request: Request):
        """List available MCP resources."""
        if not self.mcp_client_manager:
            raise HTTPException(status_code=501, detail="MCP client not available")
        
        server_name = request.query_params.get("server")
        resources = await self.mcp_client_manager.list_resources(server_name)
        
        return JSONResponse(content={
            "resources": [
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mimeType,
                    "server": resource.metadata.get("server") if resource.metadata else server_name
                }
                for resource in resources
            ]
        })
    
    async def handle_mcp_read_resource(self, request: Request):
        """Read an MCP resource."""
        if not self.mcp_client_manager:
            raise HTTPException(status_code=501, detail="MCP client not available")
        
        data = await request.json()
        server_name = data.get("server")
        uri = data.get("uri")
        
        if not server_name or not uri:
            raise HTTPException(status_code=400, detail="Missing 'server' or 'uri' parameter")
        
        try:
            contents = await self.mcp_client_manager.read_resource(server_name, uri)
            return JSONResponse(content={
                "contents": [
                    {"text": content.text} if hasattr(content, 'text') else {"data": str(content)}
                    for content in contents
                ]
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    def _get_or_create_a2a_agent(self, request: Request):
        """Get or create the A2A agent instance with current request context."""
        if not self.enable_a2a_agent or not VACA2AAgent:
            return None
        
        if self.vac_a2a_agent is None:
            base_url = str(request.base_url).rstrip('/')
            self.vac_a2a_agent = VACA2AAgent(
                base_url=base_url,
                stream_interpreter=self.stream_interpreter,
                vac_interpreter=self.vac_interpreter,
                vac_names=self.a2a_vac_names
            )
        
        return self.vac_a2a_agent
    
    async def handle_a2a_agent_card(self, request: Request):
        """Handle A2A agent card discovery request."""
        agent = self._get_or_create_a2a_agent(request)
        if not agent:
            raise HTTPException(status_code=501, detail="A2A agent not enabled")
        
        return JSONResponse(content=agent.get_agent_card())
    
    async def handle_a2a_task_send(self, request: Request):
        """Handle A2A task send request."""
        agent = self._get_or_create_a2a_agent(request)
        if not agent:
            raise HTTPException(status_code=501, detail="A2A agent not enabled")
        
        try:
            data = await request.json()
            response = await agent.handle_task_send(data)
            return JSONResponse(content=response)
        except Exception as e:
            log.error(f"A2A task send error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": data.get("id") if 'data' in locals() else None
                },
                status_code=500
            )
    
    async def handle_a2a_task_send_subscribe(self, request: Request):
        """Handle A2A task send with subscription (SSE)."""
        agent = self._get_or_create_a2a_agent(request)
        if not agent:
            raise HTTPException(status_code=501, detail="A2A agent not enabled")
        
        try:
            data = await request.json()
            
            async def sse_generator():
                async for chunk in agent.handle_task_send_subscribe(data):
                    yield chunk
            
            return StreamingResponse(
                sse_generator(),
                media_type='text/event-stream'
            )
            
        except Exception as e:
            log.error(f"A2A task send subscribe error: {e}")
            error_message = str(e)
            
            async def error_generator():
                yield f"data: {{\"error\": \"Internal error: {error_message}\"}}\n\n"
            
            return StreamingResponse(
                error_generator(),
                media_type='text/event-stream'
            )
    
    async def handle_a2a_task_get(self, request: Request):
        """Handle A2A task get request."""
        agent = self._get_or_create_a2a_agent(request)
        if not agent:
            raise HTTPException(status_code=501, detail="A2A agent not enabled")
        
        try:
            data = await request.json()
            response = await agent.handle_task_get(data)
            return JSONResponse(content=response)
        except Exception as e:
            log.error(f"A2A task get error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": data.get("id") if 'data' in locals() else None
                },
                status_code=500
            )
    
    async def handle_a2a_task_cancel(self, request: Request):
        """Handle A2A task cancel request."""
        agent = self._get_or_create_a2a_agent(request)
        if not agent:
            raise HTTPException(status_code=501, detail="A2A agent not enabled")
        
        try:
            data = await request.json()
            response = await agent.handle_task_cancel(data)
            return JSONResponse(content=response)
        except Exception as e:
            log.error(f"A2A task cancel error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": data.get("id") if 'data' in locals() else None
                },
                status_code=500
            )
    
    async def handle_a2a_push_notification(self, request: Request):
        """Handle A2A push notification settings."""
        agent = self._get_or_create_a2a_agent(request)
        if not agent:
            raise HTTPException(status_code=501, detail="A2A agent not enabled")
        
        try:
            data = await request.json()
            response = await agent.handle_push_notification_set(data)
            return JSONResponse(content=response)
        except Exception as e:
            log.error(f"A2A push notification error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": data.get("id") if 'data' in locals() else None
                },
                status_code=500
            )
    
    # MCP Tool Registration Methods
    
    def _register_custom_tools(self):
        """Register any custom tools that were added before MCP server initialization."""
        if self.vac_mcp_server:
            for tool_func, name, description in self._custom_mcp_tools:
                self.vac_mcp_server.add_tool(tool_func, name, description)
            for resource_func, name, description in self._custom_mcp_resources:
                self.vac_mcp_server.add_resource(resource_func, name, description)
    
    def add_mcp_tool(self, func: Callable, name: str = None, description: str = None):
        """
        Add a custom MCP tool to the server.
        
        Args:
            func: The tool function
            name: Optional custom name for the tool
            description: Optional description (uses docstring if not provided)
            
        Example:
            @app.add_mcp_tool
            async def my_custom_tool(param: str) -> str:
                '''Custom tool that does something useful.'''
                return f"Result: {param}"
            
            # Or with custom name and description
            app.add_mcp_tool(my_function, "custom_name", "Custom description")
        """
        if self.vac_mcp_server:
            self.vac_mcp_server.add_tool(func, name, description)
        else:
            # Store for later registration
            self._custom_mcp_tools.append((func, name, description))
        
        return func  # Allow use as decorator
    
    def add_mcp_resource(self, func: Callable, name: str = None, description: str = None):
        """
        Add a custom MCP resource to the server.
        
        Args:
            func: The resource function
            name: Optional custom name for the resource
            description: Optional description (uses docstring if not provided)
            
        Example:
            @app.add_mcp_resource
            async def my_custom_resource(uri: str) -> str:
                '''Custom resource that provides data.'''
                return f"Resource data for: {uri}"
        """
        if self.vac_mcp_server:
            self.vac_mcp_server.add_resource(func, name, description)
        else:
            # Store for later registration
            self._custom_mcp_resources.append((func, name, description))
        
        return func  # Allow use as decorator
    
    def get_mcp_server(self):
        """
        Get the MCP server instance for advanced customization.
        
        Returns:
            VACMCPServer instance or None if MCP server is not enabled
        """
        return self.vac_mcp_server
    
    def list_mcp_tools(self) -> List[str]:
        """
        List all registered MCP tools.
        
        Returns:
            List of tool names
        """
        if self.vac_mcp_server:
            return self.vac_mcp_server.list_tools()
        return []
    
    def list_mcp_resources(self) -> List[str]:
        """
        List all registered MCP resources.
        
        Returns:
            List of resource names
        """
        if self.vac_mcp_server:
            return self.vac_mcp_server.list_resources()
        return []
    
    async def handle_mcp_debug(self):
        """
        Debug endpoint to check MCP server status and list tools.
        
        Returns:
            JSON with MCP server status, tools list, and diagnostic information
        """
        import json
        
        has_mcp = self.vac_mcp_server is not None
        mcp_tools = []
        mcp_response = None
        
        # Try to call the MCP endpoint the same way clients do
        if has_mcp:
            try:
                # Make internal request to MCP server to get tools
                import httpx
                
                # Get the base URL from the current request
                from fastapi import Request
                from starlette.requests import Request as StarletteRequest
                
                # Try common ports since we don't have request context
                ports_to_try = [8000, 8001, 8080, 3000, 1956]
                successful_response = None
                
                for port in ports_to_try:
                    try:
                        base_url = f"http://localhost:{port}"
                        async with httpx.AsyncClient(timeout=2.0) as client:
                                response = await client.post(
                                    f"{base_url}/mcp/mcp",
                                    json={
                                        "jsonrpc": "2.0",
                                        "id": 1,
                                        "method": "tools/list"
                                    },
                                    headers={
                                        "Content-Type": "application/json",
                                        "Accept": "application/json, text/event-stream"
                                    }
                                )
                                
                                if response.status_code == 200:
                                    successful_response = response
                                    break  # Found working port
                    except (httpx.ConnectError, httpx.TimeoutException):
                        continue  # Try next port
                    except Exception:
                        continue  # Try next port
                
                if successful_response:
                    # Parse SSE (Server-Sent Events) response
                    text = successful_response.text
                    for line in text.split('\n'):
                        if line.startswith('data: '):
                            # Extract JSON from the data line
                            json_str = line[6:]  # Remove 'data: ' prefix
                            try:
                                mcp_response = json.loads(json_str)
                                if "result" in mcp_response and "tools" in mcp_response["result"]:
                                    for tool in mcp_response["result"]["tools"]:
                                        mcp_tools.append({
                                            "name": tool.get("name"),
                                            "description": tool.get("description", "No description")[:100] + "..." if len(tool.get("description", "")) > 100 else tool.get("description", "No description")
                                        })
                                break  # We found the data we need
                            except json.JSONDecodeError:
                                continue
                else:
                    mcp_response = {
                        "error": "Could not connect to MCP server on any common port",
                        "ports_tried": ports_to_try
                    }
                        
            except Exception as e:
                log.error(f"Error calling MCP endpoint in debug: {e}")
                mcp_response = {"error": str(e)}
                
                # Fallback: try to get tools from internal MCP server state
                try:
                    # Get tools from the FastMCP server directly
                    if hasattr(self.vac_mcp_server, 'server'):
                        mcp_server = self.vac_mcp_server.server
                        if hasattr(mcp_server, '_tools'):
                            for tool_name, tool_func in mcp_server._tools.items():
                                mcp_tools.append({
                                    "name": tool_name,
                                    "description": getattr(tool_func, '__doc__', 'No description') or 'No description'
                                })
                except Exception as inner_e:
                    log.error(f"Error getting MCP tools from internal state: {inner_e}")
        
        # Check for pending tools that haven't been registered yet
        pending_tools = len(self._custom_mcp_tools) if hasattr(self, '_custom_mcp_tools') else 0
        
        return {
            "mcp_enabled": has_mcp,
            "has_mcp_server": has_mcp,
            "mcp_tools_count": len(mcp_tools),
            "mcp_tools": [tool["name"] for tool in mcp_tools] if mcp_tools else [],
            "tool_details": mcp_tools,
            "pending_tools": pending_tools,
            "message": f"MCP server is available at /mcp endpoint with {len(mcp_tools)} tools" if has_mcp and mcp_tools else "MCP server is available at /mcp endpoint" if has_mcp else "MCP server not configured",
            "debug_info": {
                "mcp_server_type": type(self.vac_mcp_server).__name__ if self.vac_mcp_server else None,
                "has_custom_tools": len(self._custom_mcp_tools) > 0 if hasattr(self, '_custom_mcp_tools') else False,
                "has_custom_resources": len(self._custom_mcp_resources) > 0 if hasattr(self, '_custom_mcp_resources') else False
            }
        }