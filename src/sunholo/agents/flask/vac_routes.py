import json
import traceback
import datetime
import uuid
import random
from functools import partial
import inspect
import asyncio
from typing import Dict, List, Optional, Callable, Any


from ..chat_history import extract_chat_history_with_cache, extract_chat_history_async_cached
from ...qna.parsers import parse_output
from ...streaming import start_streaming_chat, start_streaming_chat_async
from ...archive import archive_qa
from ...custom_logging import log
from ...utils import ConfigManager
from ...utils.version import sunholo_version
import os
from ...gcs.add_file import add_file_to_gcs, handle_base64_image
from ..swagger import validate_api_key
from datetime import timedelta

try:
    from flask import request, jsonify, Response
except ImportError:
    pass 

try:
    from ...pubsub import PubSubManager
except ImportError:
    PubSubManager = None

try:
    from ...mcp.mcp_manager import MCPClientManager
except ImportError:
    MCPClientManager = None

try:
    from ...mcp.vac_mcp_server import VACMCPServer
    from mcp.server.models import InitializationOptions
    from mcp import JSONRPCMessage, ErrorData, INTERNAL_ERROR
except ImportError:
    VACMCPServer = None
    InitializationOptions = None
    JSONRPCMessage = None

try:
    from ...a2a.vac_a2a_agent import VACA2AAgent
except (ImportError, SyntaxError):
    VACA2AAgent = None


# Cache dictionary to store validated API keys
api_key_cache = {}
cache_duration = timedelta(minutes=5)  # Cache duration

class VACRoutes:
    """
**Usage Example:**

```python
from agents.flask import VACRoutes

app = Flask(__name__)

def stream_interpreter(question, vector_name, chat_history, **kwargs):
    # Implement your streaming logic
    ...

def vac_interpreter(question, vector_name, chat_history, **kwargs):
    # Implement your static VAC logic
    ...

vac_routes = VACRoutes(app, stream_interpreter, vac_interpreter)

if __name__ == "__main__":
    app.run(debug=True)
```
    
    """
    def __init__(self, app, 
                 stream_interpreter: callable, 
                 vac_interpreter:callable=None, 
                 additional_routes:dict=None, 
                 mcp_servers: List[Dict[str, Any]] = None,
                 async_stream:bool=False,
                 add_langfuse_eval:bool=True,
                 enable_mcp_server:bool=False,
                 enable_a2a_agent:bool=False,
                 a2a_vac_names: List[str] = None):
        self.app = app
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter or partial(self.vac_interpreter_default)

        # MCP client initialization
        self.mcp_servers = mcp_servers or []
        self.mcp_client_manager = MCPClientManager()    
        # Initialize MCP connections
        if self.mcp_servers and self.mcp_client_manager:
            asyncio.create_task(self._initialize_mcp_servers())

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
        if self.enable_a2a_agent and VACA2AAgent:
            # Extract base URL from request context during route handling
            # For now, initialize with placeholder - will be updated in route handlers
            self.vac_a2a_agent = None  # Initialized lazily in route handlers

        self.additional_routes = additional_routes if additional_routes is not None else []
        self.async_stream = async_stream
        self.add_langfuse_eval = add_langfuse_eval
        self.register_routes()
        

    def vac_interpreter_default(self, question: str, vector_name: str, chat_history=[], **kwargs):
        # Create a callback that does nothing for streaming if you don't want intermediate outputs
        class NoOpCallback:
            def on_llm_new_token(self, token):
                pass
            def on_llm_end(self, response):
                pass

        # Use the NoOpCallback for non-streaming behavior
        callback = NoOpCallback()

        # Pass all arguments to vac_stream and use the final return
        result = self.stream_interpreter(
            question=question, 
            vector_name=vector_name, 
            chat_history=chat_history, 
            callback=callback, 
            **kwargs
        )

        return result

    def register_routes(self):
        """
        Registers all the VAC routes for the Flask application.
        """
        # Basic routes
        self.app.route("/", methods=['GET'])(self.home)
        self.app.route("/health", methods=['GET'])(self.health)
        
        if self.async_stream:  # Use async treatment
            log.info("async_stream enabled")
            self.app.route('/vac/streaming/<vector_name>', 
                        methods=['POST'], 
                        provide_automatic_options=False)(self.handle_stream_vac_async)
        else:
            self.app.route('/vac/streaming/<vector_name>', 
                        methods=['POST'], 
                        provide_automatic_options=False)(self.handle_stream_vac)
        # Static VAC
        self.app.route('/vac/<vector_name>', 
                       methods=['POST'], 
                       provide_automatic_options=False)(self.handle_process_vac)

        # Authentication middleware
        self.app.before_request(self.check_authentication)

        # Handle OPTIONS requests explicitly
        self.app.route('/vac/streaming/<vector_name>', methods=['OPTIONS'])(self.handle_options)
        self.app.route('/vac/<vector_name>', methods=['OPTIONS'])(self.handle_options)

        # OpenAI health endpoint
        self.app.route('/openai/health', methods=['GET', 'POST'])(self.openai_health_endpoint)

        # OpenAI compatible endpoint
        self.app.route('/openai/v1/chat/completions', methods=['POST'])(self.handle_openai_compatible_endpoint)
        self.app.route('/openai/v1/chat/completions/<vector_name>', methods=['POST'])(self.handle_openai_compatible_endpoint)

        # MCP client routes
        if self.mcp_servers:
            self.app.route('/mcp/tools', methods=['GET'])(self.handle_mcp_list_tools)
            self.app.route('/mcp/tools/<server_name>', methods=['GET'])(self.handle_mcp_list_tools)
            self.app.route('/mcp/call', methods=['POST'])(self.handle_mcp_call_tool)
            self.app.route('/mcp/resources', methods=['GET'])(self.handle_mcp_list_resources)
            self.app.route('/mcp/resources/read', methods=['POST'])(self.handle_mcp_read_resource)
        
        # MCP server endpoint
        if self.enable_mcp_server and self.vac_mcp_server:
            self.app.route('/mcp', methods=['POST', 'GET'])(self.handle_mcp_server)
        
        # A2A agent endpoints
        if self.enable_a2a_agent:
            self.app.route('/.well-known/agent.json', methods=['GET'])(self.handle_a2a_agent_card)
            self.app.route('/a2a/tasks/send', methods=['POST'])(self.handle_a2a_task_send)
            self.app.route('/a2a/tasks/sendSubscribe', methods=['POST'])(self.handle_a2a_task_send_subscribe)
            self.app.route('/a2a/tasks/get', methods=['POST'])(self.handle_a2a_task_get)
            self.app.route('/a2a/tasks/cancel', methods=['POST'])(self.handle_a2a_task_cancel)
            self.app.route('/a2a/tasks/pushNotification/set', methods=['POST'])(self.handle_a2a_push_notification)
    
        self.register_additional_routes()

        self.app.after_request(self.register_after_request)

    def handle_options(self, **kwargs):
        response = Response(status=200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        # Reflect the request's `Access-Control-Request-Headers`
        request_headers = request.headers.get('Access-Control-Request-Headers', '')
        response.headers.add('Access-Control-Allow-Headers', request_headers)

        # Specify allowed methods
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        log.info(f'OPTION Request headers: {request_headers}')

        return response

    def register_after_request(self, response):
        # Ensure correct CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, x-api-key'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        
        return response

    def register_additional_routes(self):
        """
        Registers additional custom routes provided during initialization.

        Example:
        ```python
        from flask import Flask, jsonify
        from agents.flask import VACRoutes

        app = Flask(__name__)

        def stream_interpreter(question, vector_name, chat_history, **kwargs):
            # Implement your streaming logic
            ...

        def vac_interpreter(question, vector_name, chat_history, **kwargs):
            # Implement your static VAC logic
            ...

        def custom_handler():
            return jsonify({"message": "Custom route!"})

        custom_routes = [
            {
                "rule": "/custom",
                "methods": ["GET"],
                "handler": custom_handler
            }
        ]

        vac_routes = VACRoutes(app, stream_interpreter, vac_interpreter, additional_routes=custom_routes)

        if __name__ == "__main__":
            app.run(debug=True)
        ```
        """
        for route in self.additional_routes:
            self.app.route(route["rule"], methods=route["methods"])(route["handler"])

    def home(self):
        return jsonify("OK")

    def health(self):
        return jsonify({"status": "healthy"})
    
    def make_openai_response(self, user_message, vector_name, answer):
        response_id = str(uuid.uuid4())
        log.info("openai response: Q: {user_message} to VECTOR_NAME: {vector_name} - A: {answer}")
        openai_response = {
            "id": response_id,
            "object": "chat.completion",
            "created": str(int(datetime.datetime.now().timestamp())),
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

        log.info(f"OpenAI response: {openai_response}")
        return jsonify(openai_response)
        
    def handle_stream_vac(self, vector_name):
        observed_stream_interpreter = self.stream_interpreter
        is_async = inspect.iscoroutinefunction(self.stream_interpreter)

        if is_async:
            log.info(f"Stream interpreter is async: {observed_stream_interpreter}")

        prep = self.prep_vac(request, vector_name)
        log.info(f"Processing prep: {prep}")
        trace = prep["trace"]
        span = prep["span"]
        vac_config = prep["vac_config"]
        all_input = prep["all_input"]

        log.info(f'Streaming data with: {all_input}')
        if span:
            span.update(
                name="start_streaming_chat",
                metadata=vac_config.configs_by_kind,
                input=all_input
            )

        def generate_response_content():
            try:
                if is_async:
                    from queue import Queue, Empty
                    result_queue = Queue()
                    import threading

                    def run_async():
                        async def process_async():
                            try:
                                async_gen = start_streaming_chat_async(
                                    question=all_input["user_input"],
                                    vector_name=vector_name,
                                    qna_func_async=observed_stream_interpreter,
                                    chat_history=all_input["chat_history"],
                                    wait_time=all_input["stream_wait_time"],
                                    timeout=all_input["stream_timeout"],
                                    trace_id=trace.id if trace else None,
                                    **all_input["kwargs"]
                                )
                                log.info(f"{async_gen=}")
                                async for chunk in async_gen:
                                    if isinstance(chunk, dict) and 'answer' in chunk:
                                        if trace:
                                            chunk["trace_id"] = trace.id
                                            chunk["trace_url"] = trace.get_trace_url()
                                            span.end(output=json.dumps(chunk))
                                            trace.update(output=json.dumps(chunk))
                                        archive_qa(chunk, vector_name)
                                        result_queue.put(json.dumps(chunk))
                                    else:
                                        result_queue.put(chunk)
                            except Exception as e:
                                result_queue.put(f"Streaming Error: {str(e)} {traceback.format_exc()}")
                            finally:
                                result_queue.put(None)  # Sentinel
                        asyncio.run(process_async())

                    thread = threading.Thread(target=run_async)
                    thread.start()

                    # Read from the queue and yield results
                    while True:
                        chunk = result_queue.get()
                        if chunk is None:
                            break
                        yield chunk

                    thread.join()
                else:
                    log.info("sync streaming response")
                    for chunk in start_streaming_chat(
                        question=all_input["user_input"],
                        vector_name=vector_name,
                        qna_func=observed_stream_interpreter,
                        chat_history=all_input["chat_history"],
                        wait_time=all_input["stream_wait_time"],
                        timeout=all_input["stream_timeout"],
                        trace_id=trace.id if trace else None,
                        **all_input["kwargs"]
                    ):
                        if isinstance(chunk, dict) and 'answer' in chunk:
                            if trace:
                                chunk["trace_id"] = trace.id
                                chunk["trace_url"] = trace.get_trace_url()
                            archive_qa(chunk, vector_name)
                            if trace:
                                span.end(output=json.dumps(chunk))
                                trace.update(output=json.dumps(chunk))
                            yield json.dumps(chunk)
                        else:
                            yield chunk

            except Exception as e:
                yield f"Streaming Error: {str(e)} {traceback.format_exc()}"

        # Here, the generator function will handle streaming the content to the client.
        response = Response(generate_response_content(), content_type='text/plain; charset=utf-8')
        response.headers['Transfer-Encoding'] = 'chunked'

        log.debug(f"streaming response: {response}")
        if trace:
            span.end(output=response)
            trace.update(output=response)
            self.langfuse_eval_response(trace_id=trace.id, eval_percent=all_input.get('eval_percent'))

        return response

    async def handle_stream_vac_async(self, vector_name):
        observed_stream_interpreter = self.stream_interpreter
        is_async = inspect.iscoroutinefunction(self.stream_interpreter)

        if not is_async:
            raise ValueError(f"Stream interpreter must be async: {observed_stream_interpreter}")

        # Use the async version of prep_vac
        prep = await self.prep_vac_async(request, vector_name)
        log.info(f"Processing async prep: {prep}")
        all_input = prep["all_input"]

        log.info(f'Streaming async data with: {all_input}')

        async def generate_response_content():
            try:
                # Direct async handling without the queue/thread approach
                async_gen = start_streaming_chat_async(
                    question=all_input["user_input"],
                    vector_name=vector_name,
                    qna_func_async=observed_stream_interpreter,
                    chat_history=all_input["chat_history"],
                    wait_time=all_input["stream_wait_time"],
                    timeout=all_input["stream_timeout"],
                    **all_input["kwargs"]
                )
                
                log.info(f"{async_gen=}")
                async for chunk in async_gen:
                    if isinstance(chunk, dict) and 'answer' in chunk:
                        await archive_qa(chunk, vector_name)
                        yield json.dumps(chunk)
                    else:
                        yield chunk

            except Exception as e:
                yield f"Streaming async Error: {str(e)} {traceback.format_exc()}"

        response = Response(generate_response_content(), content_type='text/plain; charset=utf-8')
        response.headers['Transfer-Encoding'] = 'chunked'

        log.debug(f"streaming async response: {response}")

        return response

    @staticmethod
    async def _async_generator_to_stream(async_gen_func):
        """Helper function to stream the async generator's values to the client."""
        async for item in async_gen_func():
            yield item
    
    def langfuse_eval_response(self, trace_id, eval_percent=0.01):
        """
        Sends an evaluation message based on a probability defined by eval_percent.
        
        Args:
            eval_percent (float): The probability (0 to 1) of triggering the evaluation.
            trace_id (str): The trace identifier for the evaluation.
        
        Returns:
            None
        """
        if eval_percent > 1 or eval_percent < 0:
            raise ValueError("eval_percent must be a float between 0 and 1.")

        # Generate a random float between 0 and 1
        random_value = random.random()
        log.info(f"Eval: {trace_id=} {eval_percent=} / {random_value=}")
        # Check if evaluation should be triggered
        if random_value < eval_percent:
            if PubSubManager:
                try:
                    log.info(f"Publishing for eval {trace_id=}")
                    pubsub_manager = PubSubManager("langfuse_evals", pubsub_topic="topicid-to-langfuse-eval")
                    the_data = {"trace_id": trace_id}
                    pubsub_manager.publish_message(the_data)
                except Exception as e:
                    log.warning(f"Could not publish message for 'langfuse_evals' to topicid-to-langfuse-eval - {str(e)}")
        else:
            log.info(f"Did not do Langfuse eval due to random sampling not passed: {eval_percent=}")

    def handle_process_vac(self, vector_name):
        #TODO: handle async
        observed_vac_interpreter = self.vac_interpreter
        prep = self.prep_vac(request, vector_name)
        log.debug(f"Processing prep: {prep}")
        trace = prep["trace"]
        span = prep["span"]
        vac_config: ConfigManager = prep["vac_config"]
        all_input = prep["all_input"]

        try:
            if span:
                gen = span.generation(
                    name="vac_interpreter",
                    metadata=vac_config.configs_by_kind,
                    input = all_input,
                    model=vac_config.vacConfig("model") or vac_config.vacConfig("llm")
                )
            bot_output = observed_vac_interpreter(
                question=all_input["user_input"],
                vector_name=vector_name,
                chat_history=all_input["chat_history"],
                trace_id=trace.id if trace else None,
                **all_input["kwargs"]
            )
            if span:
                gen.end(output=bot_output)
            # {"answer": "The answer", "source_documents": [{"page_content": "The page content", "metadata": "The metadata"}]}
            bot_output = parse_output(bot_output)
            if trace:
                bot_output["trace_id"] = trace.id
                bot_output["trace_url"] = trace.get_trace_url()
            archive_qa(bot_output, vector_name)
            log.info(f'==LLM Q:{all_input["user_input"]} - A:{bot_output}')


        except Exception as err: 
            bot_output = {'answer': f'QNA_ERROR: An error occurred while processing /vac/{vector_name}: {str(err)} traceback: {traceback.format_exc()}'}
            if span:
                gen.end(output=bot_output)

        if trace:
            span.end(output=jsonify(bot_output))
            trace.update(output=jsonify(bot_output)) 
            self.langfuse_eval_response(trace_id=trace.id, eval_percent=all_input.get('eval_percent'))

        # {'answer': 'output'}
        return jsonify(bot_output)

    def check_authentication(self):
        if request.path.startswith('/openai/'):
            log.debug(f'Request headers: {request.headers}')
            # the header forwarded
            auth_header = request.headers.get('X-Forwarded-Authorization')
            if auth_header:
                
                if auth_header.startswith('Bearer '):
                    api_key = auth_header.split(' ')[1]  # Assuming "Bearer <api_key>"
                else:
                    return jsonify({'error': 'Invalid authorization header does not start with "Bearer " - got: {auth_header}'}), 401
                
                endpoints_host = os.getenv('_ENDPOINTS_HOST')
                if not endpoints_host:
                    return jsonify({'error': '_ENDPOINTS_HOST environment variable not found'}), 401
                
                # Check cache first
                current_time = datetime.datetime.now()
                if api_key in api_key_cache:
                    cached_result, cache_time = api_key_cache[api_key]
                    if current_time - cache_time < cache_duration:
                        if not cached_result:
                            return jsonify({'error': 'Invalid cached API key'}), 401
                        else:
                            return  # Valid API key, continue to the endpoint
                    else:
                        # Cache expired, remove from cache
                        del api_key_cache[api_key]
                
                # Validate API key
                is_valid = validate_api_key(api_key, endpoints_host)
                # Update cache
                api_key_cache[api_key] = (is_valid, current_time)
                
                if not is_valid:
                    return jsonify({'error': 'Invalid API key'}), 401
            else:
                return jsonify({'error': 'Missing Authorization header'}), 401

    def openai_health_endpoint():
            return jsonify({'message': 'Success'})

    def handle_openai_compatible_endpoint(self, vector_name=None):
        data = request.get_json()
        log.info(f'openai_compatible_endpoint got data: {data} for vector: {vector_name}')

        vector_name = vector_name or data.pop('model', None)
        messages = data.pop('messages', None)
        chat_history = data.pop('chat_history', None)
        stream = data.pop('stream', False)

        if not messages:
            return jsonify({"error": "No messages provided"}), 400

        user_message = None
        image_uri = None
        mime_type = None

        for msg in reversed(messages):
            if msg['role'] == 'user':
                if isinstance(msg['content'], list):
                    for content_item in msg['content']:
                        if content_item['type'] == 'text':
                            user_message = content_item['text']
                        elif content_item['type'] == 'image_url':
                            base64_data = content_item['image_url']['url']
                            image_uri, mime_type = handle_base64_image(base64_data, vector_name)
                else:
                    user_message = msg['content']
                break

        if not user_message:
            return jsonify({"error": "No user message provided"}), 400
        else:
            log.info(f"User message: {user_message}")
    
        if image_uri:
            data["image_uri"] = image_uri
            data["mime"] = mime_type

        all_input = {
            "user_input": user_message,
            "chat_history": chat_history,
            "kwargs": data
        }

        observed_stream_interpreter = self.stream_interpreter

        response_id = str(uuid.uuid4())
        
        def generate_response_content():
            for chunk in start_streaming_chat(question=user_message,
                                            vector_name=vector_name,
                                            qna_func=observed_stream_interpreter,
                                            chat_history=all_input["chat_history"],
                                            wait_time=all_input.get("stream_wait_time", 1),
                                            timeout=all_input.get("stream_timeout", 60),
                                            trace_id=all_input.get("trace_id"),
                                            **all_input["kwargs"]
                                            ):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    openai_chunk = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": str(int(datetime.datetime.now().timestamp())),
                        "model": vector_name,
                        "system_fingerprint": sunholo_version(),
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk['answer']},
                            "logprobs": None,
                            "finish_reason": None
                        }]
                    }
                    yield json.dumps(openai_chunk) + "\n"
                else:
                    log.info(f"Unknown chunk: {chunk}")

            final_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": str(int(datetime.datetime.now().timestamp())),
                "model": vector_name,
                "system_fingerprint": sunholo_version(),
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "logprobs": None,
                    "finish_reason": "stop"
                }]
            }
            yield json.dumps(final_chunk) + "\n"

        if stream:
            log.info("Streaming openai chunks")
            return Response(generate_response_content(), content_type='text/plain; charset=utf-8')

        try:
            observed_vac_interpreter = self.vac_interpreter
            bot_output = observed_vac_interpreter(
                question=user_message,
                vector_name=vector_name,
                chat_history=all_input["chat_history"],
                **all_input["kwargs"]
            )
            bot_output = parse_output(bot_output)

            log.info(f"Bot output: {bot_output}")
            if bot_output:
                return self.make_openai_response(user_message, vector_name, bot_output.get('answer', ''))
            else:
                return self.make_openai_response(user_message, vector_name, 'ERROR: could not find an answer')

        except Exception as err:
            log.error(f"OpenAI response error: {str(err)} traceback: {traceback.format_exc()}")
        
            return self.make_openai_response(user_message, vector_name, f'ERROR: {str(err)}')


    def create_langfuse_trace(self, request, vector_name, trace_id):
        try:
            from langfuse import Langfuse
            langfuse = Langfuse()
        except ImportError as err:
            print(f"No langfuse installed for agents.flask.register_qna_routes, install via `pip install sunholo[http]` - {str(err)}")
            
            return None

        user_id = request.headers.get("X-User-ID")
        session_id = request.headers.get("X-Session-ID")
        message_source = request.headers.get("X-Message-Source")

        package_version = sunholo_version()
        tags = [package_version, "autogenerated"]
        if message_source:
            tags.append(message_source)

        return langfuse.trace(
            id=trace_id, 
            name = f"/vac/{vector_name}",
            user_id = user_id,
            session_id = session_id,
            tags = tags,
            release = package_version
        )

    def prep_vac(self, request, vector_name):

        if request.content_type.startswith('application/json'):
            data = request.get_json()
        elif request.content_type.startswith('multipart/form-data'):
            data = request.form.to_dict()
            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    log.info(f"Found file: {file.filename} to upload to GCS")
                    try:
                        image_uri, mime_type = self.handle_file_upload(file, vector_name)
                        data["image_uri"] = image_uri
                        data["mime"] = mime_type
                    except Exception as e:
                        log.error(traceback.format_exc())
                        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
                else:
                    log.error("No file selected")
                    return jsonify({"error": "No file selected"}), 400
        else:
            return jsonify({"error": "Unsupported content type"}), 400

        log.info(f"vac/{vector_name} got data: {data}")

        trace = None
        span = None
        if self.add_langfuse_eval:
            trace_id = data.get('trace_id')
            trace = self.create_langfuse_trace(request, vector_name, trace_id)
            log.info(f"Using existing langfuse trace: {trace_id}")
        
        #config, _ = load_config("config/llm_config.yaml")
        try:
            vac_config = ConfigManager(vector_name)
        except Exception as e:
            raise ValueError(f"Unable to find vac_config for {vector_name} - {str(e)}")

        if trace:
            this_vac_config = vac_config.configs_by_kind.get("vacConfig")
            metadata_config=None
            if this_vac_config:
                metadata_config = this_vac_config.get(vector_name)

            trace.update(input=data, metadata=metadata_config)

        user_input = data.pop('user_input').strip()
        stream_wait_time = data.pop('stream_wait_time', 7)
        stream_timeout = data.pop('stream_timeout', 120)
        chat_history = data.pop('chat_history', None)
        eval_percent = data.pop('eval_percent', 0.01)
        vector_name = data.pop('vector_name', vector_name)
        data.pop('trace_id', None) # to ensure not in kwargs

        paired_messages = extract_chat_history_with_cache(chat_history)

        all_input = {'user_input': user_input, 
                     'vector_name': vector_name, 
                     'chat_history': paired_messages, 
                     'stream_wait_time': stream_wait_time,
                     'stream_timeout': stream_timeout,
                     'eval_percent': eval_percent,
                     'kwargs': data}

        if trace:
            span = trace.span(
                name="VAC",
                metadata=vac_config.configs_by_kind,
                input = all_input
            )
    
        return {
            "trace": trace,
            "span": span,
            "all_input": all_input,
            "vac_config": vac_config
        }

    async def prep_vac_async(self, request, vector_name):
        """Async version of prep_vac."""
        # Parse request data
        if request.content_type.startswith('application/json'):
            data = request.get_json()
        elif request.content_type.startswith('multipart/form-data'):
            data = request.form.to_dict()
            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    log.info(f"Found file: {file.filename} to upload to GCS")
                    try:
                        # Make file upload async if possible
                        image_uri, mime_type = await self.handle_file_upload_async(file, vector_name)
                        data["image_uri"] = image_uri
                        data["mime"] = mime_type
                    except Exception as e:
                        log.error(traceback.format_exc())
                        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
                else:
                    log.error("No file selected")
                    return jsonify({"error": "No file selected"}), 400
        else:
            return jsonify({"error": "Unsupported content type"}), 400

        log.info(f"vac/{vector_name} got data: {data}")

        # Run these operations concurrently
        tasks = []
        
        # Extract other data while configs load
        user_input = data.pop('user_input').strip()
        stream_wait_time = data.pop('stream_wait_time', 7)
        stream_timeout = data.pop('stream_timeout', 120)
        chat_history = data.pop('chat_history', None)
        vector_name_param = data.pop('vector_name', vector_name)
        data.pop('trace_id', None)  # to ensure not in kwargs
        
        # Task 3: Process chat history
        chat_history_task = asyncio.create_task(extract_chat_history_async_cached(chat_history))
        tasks.append(chat_history_task)
        
        # Await all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        paired_messages = results[0] if not isinstance(results[0], Exception) else []
        
        # Only create span after we have trace
        all_input = {
            'user_input': user_input, 
            'vector_name': vector_name_param, 
            'chat_history': paired_messages, 
            'stream_wait_time': stream_wait_time,
            'stream_timeout': stream_timeout,
            'kwargs': data
        }
        
        return {
            "all_input": all_input
        }

    def handle_file_upload(self, file, vector_name):
        try:
            file.save(file.filename)
            image_uri = add_file_to_gcs(file.filename, vector_name)
            os.remove(file.filename)  # Clean up the saved file
            return image_uri, file.mimetype
        except Exception as e:
            raise Exception(f'File upload failed: {str(e)}')

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

    
    def handle_mcp_list_tools(self, server_name: Optional[str] = None):
        """List available MCP tools."""
        async def get_tools():
            tools = await self.mcp_client_manager.list_tools(server_name)
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                    "server": tool.metadata.get("server") if tool.metadata else server_name
                }
                for tool in tools
            ]
        
        # Run async in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tools = loop.run_until_complete(get_tools())
            return jsonify({"tools": tools})
        finally:
            loop.close()
    
    def handle_mcp_call_tool(self):
        """Call an MCP tool."""
        data = request.get_json()
        server_name = data.get("server")
        tool_name = data.get("tool")
        arguments = data.get("arguments", {})
        
        if not server_name or not tool_name:
            return jsonify({"error": "Missing 'server' or 'tool' parameter"}), 400
        
        async def call_tool():
            try:
                result = await self.mcp_client_manager.call_tool(server_name, tool_name, arguments)
                
                # Convert result to JSON-serializable format
                if hasattr(result, 'content'):
                    # Handle different content types
                    if hasattr(result.content, 'text'):
                        return {"result": result.content.text}
                    elif hasattr(result.content, 'data'):
                        return {"result": result.content.data}
                    else:
                        return {"result": str(result.content)}
                else:
                    return {"result": str(result)}
                    
            except Exception as e:
                return {"error": str(e)}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(call_tool())
            if "error" in result:
                return jsonify(result), 500
            return jsonify(result)
        finally:
            loop.close()
    
    def handle_mcp_list_resources(self):
        """List available MCP resources."""
        server_name = request.args.get("server")
        
        async def get_resources():
            resources = await self.mcp_client_manager.list_resources(server_name)
            return [
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mimeType,
                    "server": resource.metadata.get("server") if resource.metadata else server_name
                }
                for resource in resources
            ]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            resources = loop.run_until_complete(get_resources())
            return jsonify({"resources": resources})
        finally:
            loop.close()
    
    def handle_mcp_read_resource(self):
        """Read an MCP resource."""
        data = request.get_json()
        server_name = data.get("server")
        uri = data.get("uri")
        
        if not server_name or not uri:
            return jsonify({"error": "Missing 'server' or 'uri' parameter"}), 400
        
        async def read_resource():
            try:
                contents = await self.mcp_client_manager.read_resource(server_name, uri)
                return {
                    "contents": [
                        {"text": content.text} if hasattr(content, 'text') else {"data": str(content)}
                        for content in contents
                    ]
                }
            except Exception as e:
                return {"error": str(e)}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(read_resource())
            if "error" in result:
                return jsonify(result), 500
            return jsonify(result)
        finally:
            loop.close()
    
    def handle_mcp_server(self):
        """Handle MCP server requests using HTTP transport."""
        if not self.vac_mcp_server:
            return jsonify({"error": "MCP server not enabled"}), 501
        
        import json as json_module
        
        # Handle streaming for HTTP transport
        if request.method == 'POST':
            try:
                # Get the JSON-RPC request
                data = request.get_json()
                log.info(f"MCP server received: {data}")
                
                # Create an async handler for the request
                async def process_request():
                    # Create mock read/write streams for the server
                    from io import StringIO
                    import asyncio
                    
                    # Convert request to proper format
                    request_str = json_module.dumps(data) + '\n'
                    
                    # Create read queue with the request
                    read_queue = asyncio.Queue()
                    await read_queue.put(request_str.encode())
                    await read_queue.put(None)  # EOF signal
                    
                    # Create write queue for response
                    write_queue = asyncio.Queue()
                    
                    # Create async iterators
                    async def read_messages():
                        while True:
                            msg = await read_queue.get()
                            if msg is None:
                                break
                            yield msg
                    
                    responses = []
                    async def write_messages():
                        async for msg in write_queue:
                            if msg is None:
                                break
                            responses.append(msg.decode())
                    
                    # Run the server with these streams
                    server = self.vac_mcp_server.get_server()
                    
                    # Start write handler
                    write_task = asyncio.create_task(write_messages())
                    
                    try:
                        # Process the request through the server
                        await server.run(
                            read_messages(),
                            write_queue,
                            InitializationOptions() if InitializationOptions else None
                        )
                    except Exception as e:
                        log.error(f"Error processing MCP request: {e}")
                        await write_queue.put(None)
                        await write_task
                        raise
                    
                    # Signal end and wait for write task
                    await write_queue.put(None)
                    await write_task
                    
                    # Return collected responses
                    return responses
                
                # Run the async handler
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    responses = loop.run_until_complete(process_request())
                    
                    # Parse and return the response
                    if responses:
                        # The response should be a single JSON-RPC response
                        response_data = json_module.loads(responses[0])
                        return jsonify(response_data)
                    else:
                        return jsonify({"error": "No response from MCP server"}), 500

                except Exception as e:
                    log.error(f"MCP server error: {str(e)}")
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        },
                        "id": data.get("id") if isinstance(data, dict) else None
                    }), 500
                finally:
                    loop.close()
                        
            except Exception as e:
                log.error(f"MCP server error: {str(e)}")
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": data.get("id") if isinstance(data, dict) else None
                }), 500
                    
        else:
            # GET request - return server information
            return jsonify({
                "name": "sunholo-vac-server",
                "version": "1.0.0",
                "transport": "http",
                "endpoint": "/mcp",
                "tools": ["vac_stream", "vac_query"] if self.vac_interpreter else ["vac_stream"]
            })
    
    def _get_or_create_a2a_agent(self):
        """Get or create the A2A agent instance with current request context."""
        if not self.enable_a2a_agent or not VACA2AAgent:
            return None
        
        if self.vac_a2a_agent is None:
            # Extract base URL from current request
            base_url = request.url_root.rstrip('/')
            
            self.vac_a2a_agent = VACA2AAgent(
                base_url=base_url,
                stream_interpreter=self.stream_interpreter,
                vac_interpreter=self.vac_interpreter,
                vac_names=self.a2a_vac_names
            )
        
        return self.vac_a2a_agent
    
    def handle_a2a_agent_card(self):
        """Handle A2A agent card discovery request."""
        agent = self._get_or_create_a2a_agent()
        if not agent:
            return jsonify({"error": "A2A agent not enabled"}), 501
        
        return jsonify(agent.get_agent_card())
    
    def handle_a2a_task_send(self):
        """Handle A2A task send request."""
        agent = self._get_or_create_a2a_agent()
        if not agent:
            return jsonify({"error": "A2A agent not enabled"}), 501
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    },
                    "id": None
                }), 400
            
            # Run async handler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(agent.handle_task_send(data))
                return jsonify(response)
            finally:
                loop.close()
                
        except Exception as e:
            log.error(f"A2A task send error: {e}")
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": data.get("id") if 'data' in locals() else None
            }), 500
    
    def handle_a2a_task_send_subscribe(self):
        """Handle A2A task send with subscription (SSE)."""
        agent = self._get_or_create_a2a_agent()
        if not agent:
            return jsonify({"error": "A2A agent not enabled"}), 501
        
        try:
            data = request.get_json()
            if not data:
                def error_generator():
                    yield "data: {\"error\": \"Parse error: Invalid JSON\"}\n\n"
                
                return Response(error_generator(), content_type='text/event-stream')
            
            # Create async generator for SSE
            async def sse_generator():
                async for chunk in agent.handle_task_send_subscribe(data):
                    yield chunk
            
            def sync_generator():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    async_gen = sse_generator()
                    while True:
                        try:
                            chunk = loop.run_until_complete(async_gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                finally:
                    loop.close()
            
            return Response(sync_generator(), content_type='text/event-stream')
            
        except Exception as e:
            log.error(f"A2A task send subscribe error: {e}")
            def error_generator(err):
                yield f"data: {{\"error\": \"Internal error: {str(err)}\"}}\n\n"
            
            return Response(error_generator(e), content_type='text/event-stream')
    
    def handle_a2a_task_get(self):
        """Handle A2A task get request."""
        agent = self._get_or_create_a2a_agent()
        if not agent:
            return jsonify({"error": "A2A agent not enabled"}), 501
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    },
                    "id": None
                }), 400
            
            # Run async handler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(agent.handle_task_get(data))
                return jsonify(response)
            finally:
                loop.close()
                
        except Exception as e:
            log.error(f"A2A task get error: {e}")
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": data.get("id") if 'data' in locals() else None
            }), 500
    
    def handle_a2a_task_cancel(self):
        """Handle A2A task cancel request."""
        agent = self._get_or_create_a2a_agent()
        if not agent:
            return jsonify({"error": "A2A agent not enabled"}), 501
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    },
                    "id": None
                }), 400
            
            # Run async handler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(agent.handle_task_cancel(data))
                return jsonify(response)
            finally:
                loop.close()
                
        except Exception as e:
            log.error(f"A2A task cancel error: {e}")
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": data.get("id") if 'data' in locals() else None
            }), 500
    
    def handle_a2a_push_notification(self):
        """Handle A2A push notification settings."""
        agent = self._get_or_create_a2a_agent()
        if not agent:
            return jsonify({"error": "A2A agent not enabled"}), 501
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    },
                    "id": None
                }), 400
            
            # Run async handler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(agent.handle_push_notification_set(data))
                return jsonify(response)
            finally:
                loop.close()
                
        except Exception as e:
            log.error(f"A2A push notification error: {e}")
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": data.get("id") if 'data' in locals() else None
            }), 500