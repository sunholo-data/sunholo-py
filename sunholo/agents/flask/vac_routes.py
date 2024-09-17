import json
import traceback
import datetime
import uuid
import random
from functools import partial
import inspect
import asyncio

from ...agents import extract_chat_history, handle_special_commands
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
    def __init__(self, app, stream_interpreter, vac_interpreter=None, additional_routes=None):
        self.app = app
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter or partial(self.vac_interpreter_default)
        self.additional_routes = additional_routes if additional_routes is not None else []
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

        # Streaming VAC
        self.app.route('/vac/streaming/<vector_name>', methods=['POST'])(self.handle_stream_vac)

        # Static VAC
        self.app.route('/vac/<vector_name>', methods=['POST'])(self.handle_process_vac)

        # Authentication middleware
        self.app.before_request(self.check_authentication)

        # OpenAI health endpoint
        self.app.route('/openai/health', methods=['GET', 'POST'])(self.openai_health_endpoint)

        # OpenAI compatible endpoint
        self.app.route('/openai/v1/chat/completions', methods=['POST'])(self.handle_openai_compatible_endpoint)
        self.app.route('/openai/v1/chat/completions/<vector_name>', methods=['POST'])(self.handle_openai_compatible_endpoint)
        # Register additional routes
        self.register_additional_routes()

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
        command_response = prep["command_response"]
        vac_config = prep["vac_config"]
        all_input = prep["all_input"]

        if command_response:
            return jsonify(command_response)

        log.info(f'Streaming data with: {all_input}')
        if span:
            generation = span.generation(
                name="start_streaming_chat",
                metadata=vac_config.configs_by_kind,
                input=all_input,
                completion_start_time=str(int(datetime.datetime.now().timestamp())),
                model=vac_config.vacConfig("model") or vac_config.vacConfig("llm")
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
                                            generation.end(output=json.dumps(chunk))
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
                                generation.end(output=json.dumps(chunk))
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
            generation.end(output=response)
            span.end(output=response)
            trace.update(output=response)
            self.langfuse_eval_response(trace_id=trace.id, eval_percent=all_input.get('eval_percent'))

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
        command_response = prep["command_response"]
        vac_config: ConfigManager = prep["vac_config"]
        all_input = prep["all_input"]

        if command_response:
            return jsonify(command_response)

        try:
            if span:
                generation = span.generation(
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
                generation.end(output=bot_output)
            # {"answer": "The answer", "source_documents": [{"page_content": "The page content", "metadata": "The metadata"}]}
            bot_output = parse_output(bot_output)
            if trace:
                bot_output["trace_id"] = trace.id
                bot_output["trace_url"] = trace.get_trace_url()
            archive_qa(bot_output, vector_name)
            log.info(f'==LLM Q:{all_input["user_input"]} - A:{bot_output}')


        except Exception as err: 
            bot_output = {'answer': f'QNA_ERROR: An error occurred while processing /vac/{vector_name}: {str(err)} traceback: {traceback.format_exc()}'}
    
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
    
        paired_messages = extract_chat_history(chat_history)
        command_response = handle_special_commands(user_message, vector_name, paired_messages)

        if command_response is not None:

            return self.make_openai_response(user_message, vector_name, command_response)
    
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
            release = f"sunholo-v{package_version}"
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

        trace_id = data.get('trace_id')
        trace = self.create_langfuse_trace(request, vector_name, trace_id)
        log.info(f"Using existing langfuse trace: {trace_id}")
        
        #config, _ = load_config("config/llm_config.yaml")
        try:
            vac_config = ConfigManager(vector_name)
        except Exception as e:
            raise ValueError(f"Unable to find vac_config for {vector_name} - {str(e)}")

        if trace:
            trace.update(input=data, metadata=vac_config.configs_by_kind)

        user_input = data.pop('user_input').strip()
        stream_wait_time = data.pop('stream_wait_time', 7)
        stream_timeout = data.pop('stream_timeout', 120)
        chat_history = data.pop('chat_history', None)
        eval_percent = data.pop('eval_percent', 0.01)
        vector_name = data.pop('vector_name', vector_name)
        data.pop('trace_id', None) # to ensure not in kwargs

        paired_messages = extract_chat_history(chat_history)

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
        command_response = handle_special_commands(user_input, vector_name, paired_messages)
        if command_response is not None:
            if trace:
                trace.update(output=jsonify(command_response))
    
        return {
            "trace": trace,
            "span": span,
            "command_response": command_response,
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


