import json
import traceback
import datetime
import uuid

from ...agents import extract_chat_history, handle_special_commands
from ...qna.parsers import parse_output
from ...streaming import start_streaming_chat
from ...archive import archive_qa
from ...logging import log
from ...utils.config import load_config
from ...utils.version import sunholo_version
import os
from ...gcs.add_file import add_file_to_gcs, handle_base64_image
from ..swagger import validate_api_key
from datetime import datetime, timedelta

try:
    from flask import request, jsonify, Response
except ImportError:
    pass

try:
    from langfuse.decorators import langfuse_context, observe
except ImportError:
    pass    

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
    def __init__(self, app, stream_interpreter, vac_interpreter):
        self.app = app
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter
        self.register_routes()

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
            "created": str(int(datetime.now().timestamp())),
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
        observed_stream_interpreter = observe()(self.stream_interpreter)
        prep = self.prep_vac(request, vector_name)
        log.debug(f"Processing prep: {prep}")
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
                metadata=vac_config,
                input = all_input,
                completion_start_time=datetime.datetime.now(),
                model=vac_config.get("model") or vac_config.get("llm")
            )

        def generate_response_content():

            for chunk in start_streaming_chat(question=all_input["user_input"],
                                                vector_name=vector_name,
                                                qna_func=observed_stream_interpreter,
                                                chat_history=all_input["chat_history"],
                                                wait_time=all_input["stream_wait_time"],
                                                timeout=all_input["stream_timeout"],
                                                #kwargs
                                                **all_input["kwargs"]
                                                ):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    # When we encounter the dictionary, we yield it as a JSON string
                    # and stop the generator.
                    if trace:
                        chunk["trace"] = trace.id
                        chunk["trace_url"] = trace.get_trace_url()
                    archive_qa(chunk, vector_name)
                    if trace:
                        generation.end(output=json.dumps(chunk))
                        span.end(output=json.dumps(chunk))
                        trace.update(output=json.dumps(chunk))

                    return json.dumps(chunk)
            
                else:
                    # Otherwise, we yield the plain text chunks as they come in.
                    yield chunk
        
        # Here, the generator function will handle streaming the content to the client.
        response = Response(generate_response_content(), content_type='text/plain; charset=utf-8')
        response.headers['Transfer-Encoding'] = 'chunked'  

        log.debug(f"streaming response: {response}")
        if trace:
            generation.end(output=response)
            span.end(output=response)
            trace.update(output=response)

        return response

    def handle_process_vac(self, vector_name):
        observed_vac_interpreter = observe()(self.vac_interpreter)
        prep = self.prep_vac(request, vector_name)
        log.debug(f"Processing prep: {prep}")
        trace = prep["trace"]
        span = prep["span"]
        command_response = prep["command_response"]
        vac_config = prep["vac_config"]
        all_input = prep["all_input"]

        if command_response:
            return jsonify(command_response)

        try:
            if span:
                generation = span.generation(
                    name="vac_interpreter",
                    metadata=vac_config,
                    input = all_input,
                    model=vac_config.get("model") or vac_config.get("llm")
                )
            bot_output = observed_vac_interpreter(
                question=all_input["user_input"],
                vector_name=vector_name,
                chat_history=all_input["chat_history"],
                **all_input["kwargs"]
            )
            if span:
                generation.end(output=bot_output)
            # {"answer": "The answer", "source_documents": [{"page_content": "The page content", "metadata": "The metadata"}]}
            bot_output = parse_output(bot_output)
            if trace:
                bot_output["trace"] = trace.id
                bot_output["trace_url"] = trace.get_trace_url()
            archive_qa(bot_output, vector_name)
            log.info(f'==LLM Q:{all_input["user_input"]} - A:{bot_output}')


        except Exception as err: 
            bot_output = {'answer': f'QNA_ERROR: An error occurred while processing /vac/{vector_name}: {str(err)} traceback: {traceback.format_exc()}'}
    
        if trace:
            span.end(output=jsonify(bot_output))
            trace.update(output=jsonify(bot_output)) 

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
                current_time = datetime.now()
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

        observed_stream_interpreter = observe()(self.stream_interpreter)

        response_id = str(uuid.uuid4())
        
        def generate_response_content():
            for chunk in start_streaming_chat(question=user_message,
                                            vector_name=vector_name,
                                            qna_func=observed_stream_interpreter,
                                            chat_history=all_input["chat_history"],
                                            wait_time=all_input.get("stream_wait_time", 1),
                                            timeout=all_input.get("stream_timeout", 60),
                                            **all_input["kwargs"]
                                            ):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    openai_chunk = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": str(int(datetime.now().timestamp())),
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
                "created": str(int(datetime.now().timestamp())),
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
            observed_vac_interpreter = observe()(self.vac_interpreter)
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


    def create_langfuse_trace(self, request, vector_name):
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
        tags = [package_version]
        if message_source:
            tags.append(message_source)

        return langfuse.trace(
            name = f"/vac/{vector_name}",
            user_id = user_id,
            session_id = session_id,
            tags = tags,
            release = f"sunholo-v{package_version}"
        )

    def prep_vac(self, request, vector_name):
        trace = self.create_langfuse_trace(request, vector_name)
        span = None

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
                        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
                else:
                    return jsonify({"error": "No file selected"}), 400
        else:
            return jsonify({"error": "Unsupported content type"}), 400

        log.info(f"vac/{vector_name} got data: {data}")

        config, _ = load_config("config/llm_config.yaml")
        vac_configs = config.get("vac")
        if vac_configs:
            vac_config = vac_configs[vector_name]

        if trace:
            trace.update(input=data, metadata=vac_config)

        user_input = data.pop('user_input').strip()
        stream_wait_time = data.pop('stream_wait_time', 7)
        stream_timeout = data.pop('stream_timeout', 120)
        chat_history = data.pop('chat_history', None)
        vector_name = data.pop('vector_name', vector_name)

        paired_messages = extract_chat_history(chat_history)

        all_input = {'user_input': user_input, 
                     'vector_name': vector_name, 
                     'chat_history': paired_messages, 
                     'stream_wait_time': stream_wait_time,
                     'stream_timeout': stream_timeout,
                     'kwargs': data}

        if trace:
            span = trace.span(
                name="VAC",
                metadata=vac_config,
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


