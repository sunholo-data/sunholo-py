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
    from ...mcp.vac_mcp_server import VACMCPServer
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
    FastAPI implementation of VAC routes with streaming support.
    
    This class provides a FastAPI-compatible version of the Flask VACRoutes,
    with proper async streaming support using callbacks.
    
    Usage Example:
    ```python
    from fastapi import FastAPI
    from sunholo.agents.fastapi import VACRoutesFastAPI
    
    app = FastAPI()
    
    async def stream_interpreter(question, vector_name, chat_history, callback, **kwargs):
        # Implement your streaming logic with callbacks
        ...
    
    async def vac_interpreter(question, vector_name, chat_history, **kwargs):
        # Implement your static VAC logic
        ...
    
    vac_routes = VACRoutesFastAPI(
        app, 
        stream_interpreter, 
        vac_interpreter,
        enable_mcp_server=True
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
        enable_mcp_server: bool = False,
        enable_a2a_agent: bool = False,
        a2a_vac_names: Optional[List[str]] = None
    ):
        """
        Initialize FastAPI VAC routes.
        
        Args:
            app: FastAPI application instance
            stream_interpreter: Async or sync function for streaming responses
            vac_interpreter: Optional function for non-streaming responses
            additional_routes: List of additional routes to register
            mcp_servers: List of MCP server configurations
            add_langfuse_eval: Whether to add Langfuse evaluation
            enable_mcp_server: Whether to enable MCP server endpoint
            enable_a2a_agent: Whether to enable A2A agent endpoints
            a2a_vac_names: List of VAC names for A2A agent
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
        
        # MCP server initialization
        self.enable_mcp_server = enable_mcp_server
        self.vac_mcp_server = None
        if self.enable_mcp_server and VACMCPServer:
            self.vac_mcp_server = VACMCPServer(
                stream_interpreter=self.stream_interpreter,
                vac_interpreter=self.vac_interpreter
            )
        
        # A2A agent initialization
        self.enable_a2a_agent = enable_a2a_agent
        self.vac_a2a_agent = None
        self.a2a_vac_names = a2a_vac_names
        
        self.additional_routes = additional_routes or []
        self.add_langfuse_eval = add_langfuse_eval
        
        self.register_routes()
    
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
        
        # MCP server endpoint
        if self.enable_mcp_server and self.vac_mcp_server:
            self.app.post("/mcp")(self.handle_mcp_server)
            self.app.get("/mcp")(self.handle_mcp_server_info)
        
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
    
    async def handle_mcp_server(self, request: Request):
        """Handle MCP server requests."""
        if not self.vac_mcp_server:
            raise HTTPException(status_code=501, detail="MCP server not enabled")
        
        data = await request.json()
        log.info(f"MCP server received: {data}")
        
        # Process MCP request - simplified version
        # Full implementation would handle all MCP protocol methods
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        try:
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "sunholo-vac-server",
                            "version": sunholo_version()
                        }
                    },
                    "id": request_id
                }
            elif method == "tools/list":
                tools = [
                    {
                        "name": "vac_stream",
                        "description": "Stream responses from a Sunholo VAC",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "vector_name": {"type": "string"},
                                "user_input": {"type": "string"},
                                "chat_history": {"type": "array", "default": []}
                            },
                            "required": ["vector_name", "user_input"]
                        }
                    }
                ]
                if self.vac_interpreter:
                    tools.append({
                        "name": "vac_query",
                        "description": "Query a Sunholo VAC (non-streaming)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "vector_name": {"type": "string"},
                                "user_input": {"type": "string"},
                                "chat_history": {"type": "array", "default": []}
                            },
                            "required": ["vector_name", "user_input"]
                        }
                    })
                response = {
                    "jsonrpc": "2.0",
                    "result": {"tools": tools},
                    "id": request_id
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "vac_stream":
                    result = await self.vac_mcp_server._handle_vac_stream(arguments)
                elif tool_name == "vac_query":
                    result = await self.vac_mcp_server._handle_vac_query(arguments)
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                response = {
                    "jsonrpc": "2.0",
                    "result": {"content": [item.model_dump() for item in result]},
                    "id": request_id
                }
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": request_id
            }
        
        return JSONResponse(content=response)
    
    async def handle_mcp_server_info(self):
        """Return MCP server information."""
        return JSONResponse(content={
            "name": "sunholo-vac-server",
            "version": "1.0.0",
            "transport": "http",
            "endpoint": "/mcp",
            "tools": ["vac_stream", "vac_query"] if self.vac_interpreter else ["vac_stream"]
        })
    
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