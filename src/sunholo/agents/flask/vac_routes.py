import json
import traceback
import datetime
import uuid
import random
from functools import partial
import inspect
import asyncio
import time
import threading
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

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

# Cache dictionary to store validated API keys
api_key_cache = {}
cache_duration = timedelta(minutes=5)  # Cache duration
# Global caches and thread pool 
_config_cache = {}
_config_lock = threading.Lock()
_thread_pool = ThreadPoolExecutor(max_workers=4)


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
                 async_stream:bool=False,
                 add_langfuse_eval:bool=True):
        self.app = app
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter or partial(self.vac_interpreter_default)
        self.additional_routes = additional_routes if additional_routes is not None else []
        self.async_stream = async_stream
        self.add_langfuse_eval = add_langfuse_eval

        # Pre-warm common configs
        self._preload_common_configs()   

        self.register_routes()

    def _preload_common_configs(self):
        """Pre-load commonly used configurations to cache"""
        common_vector_names = ["aitana3"]  # Add your common vector names 
        for vector_name in common_vector_names:
            try:
                self._get_cached_config(vector_name)
                log.info(f"Pre-loaded config for {vector_name}")
            except Exception as e:
                log.warning(f"Failed to pre-load config for {vector_name}: {e}")

    def _get_cached_config(self, vector_name: str):
        """Cached config loader with thread safety - CORRECTED VERSION"""
        # Check cache first (without lock for read)
        if vector_name in _config_cache:
            log.debug(f"Using cached config for {vector_name}")
            return _config_cache[vector_name]
        
        # Need to load config
        with _config_lock:
            # Double-check inside lock (another thread might have loaded it)
            if vector_name in _config_cache:
                return _config_cache[vector_name]
            
            try:
                log.info(f"Loading fresh config for {vector_name}")
                config = ConfigManager(vector_name)
                _config_cache[vector_name] = config
                log.info(f"Cached config for {vector_name}")
                return config
            except Exception as e:
                log.error(f"Error loading config for {vector_name}: {e}")
                raise

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

    def _finalize_trace_background(self, trace, span, response, all_input):
        """Finalize trace operations in background"""
        try:
            if span:
                span.end(output=str(response))
            if trace:
                trace.update(output=str(response))
                self.langfuse_eval_response(trace_id=trace.id, eval_percent=all_input.get('eval_percent'))
        except Exception as e:
            log.warning(f"Background trace finalization failed: {e}")

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
    
    def _create_langfuse_trace_background(self, request, vector_name, trace_id):
        """Create Langfuse trace in background"""
        try:
            return self.create_langfuse_trace(request, vector_name, trace_id)
        except Exception as e:
            log.warning(f"Background trace creation failed: {e}")
            return None

    def _handle_file_upload_background(self, file, vector_name):
        """Handle file upload in background thread"""
        try:
            # Save with timestamp to avoid conflicts
            temp_filename = f"temp_{int(time.time() * 1000)}_{file.filename}"
            file.save(temp_filename)
            
            # Upload to GCS
            image_uri = add_file_to_gcs(temp_filename, vector_name)
            
            # Clean up
            os.remove(temp_filename)
            
            return {"image_uri": image_uri, "mime": file.mimetype}
        except Exception as e:
            log.error(f"Background file upload failed: {e}")
            return {}
    
    def prep_vac(self, request, vector_name):
        start_time = time.time()
        
        # Fast request parsing - KEEP ORIGINAL ERROR HANDLING STYLE
        if request.content_type.startswith('application/json'):
            data = request.get_json()
        elif request.content_type.startswith('multipart/form-data'):
            data = request.form.to_dict()
            # Handle file upload in background if present
            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    log.info(f"Found file: {file.filename} - uploading in background")
                    # Start file upload in background, don't block
                    upload_future = _thread_pool.submit(self._handle_file_upload_background, file, vector_name)
                    data["_upload_future"] = upload_future
        else:
            # KEEP ORIGINAL STYLE - return the error response directly
            raise ValueError("Unsupported content type")

        log.info(f"vac/{vector_name} got data keys: {list(data.keys())}")

        # Get config from cache first (before processing other data)
        try:
            vac_config = self._get_cached_config(vector_name)
        except Exception as e:
            raise ValueError(f"Unable to find vac_config for {vector_name} - {str(e)}")

        # Extract data (keep original logic)
        user_input = data.pop('user_input').strip()
        stream_wait_time = data.pop('stream_wait_time', 7)
        stream_timeout = data.pop('stream_timeout', 120)
        chat_history = data.pop('chat_history', None)
        eval_percent = data.pop('eval_percent', 0.01)
        vector_name_param = data.pop('vector_name', vector_name)
        data.pop('trace_id', None)  # to ensure not in kwargs

        # Process chat history with caching
        paired_messages = extract_chat_history_with_cache(chat_history)

        # Wait for file upload if it was started (with timeout)
        if "_upload_future" in data:
            try:
                upload_result = data["_upload_future"].result(timeout=3.0)  # 3 sec max wait
                data.update(upload_result)
                log.info(f"File upload completed: {upload_result.get('image_uri', 'no uri')}")
            except Exception as e:
                log.warning(f"File upload failed or timed out: {e}")
            finally:
                data.pop("_upload_future", None)

        # BUILD all_input BEFORE trace creation (this was moved inside try/catch by mistake)
        all_input = {
            'user_input': user_input, 
            'vector_name': vector_name_param, 
            'chat_history': paired_messages, 
            'stream_wait_time': stream_wait_time,
            'stream_timeout': stream_timeout,
            'eval_percent': eval_percent,
            'kwargs': data
        }

        # Initialize trace variables
        trace = None
        span = None
        if self.add_langfuse_eval:
            trace_id = data.get('trace_id')
            # Create trace in background - don't block
            trace_future = _thread_pool.submit(self._create_langfuse_trace_background, request, vector_name, trace_id)

            # Try to get trace result if available (don't block long)
            try:
                trace = trace_future.result(timeout=0.1)  # Very short timeout
                if trace:
                    this_vac_config = vac_config.configs_by_kind.get("vacConfig")
                    metadata_config = None
                    if this_vac_config:
                        metadata_config = this_vac_config.get(vector_name)
                    trace.update(input=data, metadata=metadata_config)
                    
                    span = trace.span(
                        name="VAC",
                        metadata=vac_config.configs_by_kind,
                        input=all_input
                    )
            except Exception as e:
                log.warning(f"Langfuse trace creation timed out or failed: {e}")
                trace = None
                span = None

        prep_time = time.time() - start_time
        log.info(f"prep_vac completed in {prep_time:.3f}s")

        return {
            "trace": trace,
            "span": span,
            "all_input": all_input,
            "vac_config": vac_config
        }

    def handle_file_upload(self, file, vector_name):
        try:
            file.save(file.filename)
            image_uri = add_file_to_gcs(file.filename, vector_name)
            os.remove(file.filename)  # Clean up the saved file
            return image_uri, file.mimetype
        except Exception as e:
            raise Exception(f'File upload failed: {str(e)}')


