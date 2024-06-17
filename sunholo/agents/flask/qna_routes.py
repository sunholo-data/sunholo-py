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
from ...gcs.add_file import add_file_to_gcs


try:
    from flask import request, jsonify, Response
except ImportError:
    pass

try:
    from langfuse.decorators import langfuse_context, observe
except ImportError:
    pass    


def register_qna_routes(app, stream_interpreter, vac_interpreter):

    @app.route("/")
    def home():
        return jsonify("OK")

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"})

    @app.route('/vac/streaming/<vector_name>', methods=['POST'])
    def stream_qa(vector_name):
        observed_stream_interpreter = observe()(stream_interpreter)
        prep = prep_vac(request, vector_name)
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

    @app.route('/vac/<vector_name>', methods=['POST'])
    def process_qna(vector_name):
        observed_vac_interpreter = observe()(vac_interpreter)
        prep = prep_vac(request, vector_name)
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

    @app.route('/openai/v1/chat/completions', methods=['POST'])
    @app.route('/openai/v1/chat/completions/<vector_name>', methods=['POST'])
    def openai_compatible_endpoint(vector_name=None):
        data = request.get_json()
        log.info(f'openai_compatible_endpoint got data: {data}')

        vector_name = vector_name or data.pop('model', None)
        messages = data.pop('messages', None)
        chat_history = data.pop('chat_history', None)
        stream = data.pop('stream', False)

        log.info(f'openai_compatible_endpoint got data: {data} for vector: {vector_name}')

        if not messages:
            return jsonify({"error": "No messages provided"}), 400

        user_message = next((msg['content'] for msg in messages if msg['role'] == 'user'), None)
        if not user_message:
            return jsonify({"error": "No user message provided"}), 400

        all_input = {
            "user_input": user_message,
            "chat_history": chat_history,
            "kwargs": data
        }

        observed_stream_interpreter = observe()(stream_interpreter)


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
                        "created": str(datetime.time()),
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
                "created": str(datetime.time()),
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
            return Response(generate_response_content(), content_type='text/plain; charset=utf-8')

        try:
            bot_output = observed_stream_interpreter(
                question=user_message,
                vector_name=vector_name,
                chat_history=all_input["chat_history"],
                **all_input["kwargs"]
            )
            bot_output = parse_output(bot_output)

            openai_response = {
                "id": response_id,
                "object": "chat.completion",
                "created": str(datetime.time()),
                "model": vector_name,
                "system_fingerprint": sunholo_version(),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": bot_output.get('answer', ''),
                    },
                    "logprobs": None,
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(bot_output.get('answer', '').split()),
                    "total_tokens": len(user_message.split()) + len(bot_output.get('answer', '').split())
                }
            }

            log.info(f"OpenAI response: {openai_response}")
            return jsonify(openai_response)

        except Exception as err:
            return jsonify({'error': f'QNA_ERROR: An error occurred: {str(err)} traceback: {traceback.format_exc()}'}), 500


def create_langfuse_trace(request, vector_name):
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

def prep_vac(request, vector_name):
    #trace = create_langfuse_trace(request, vector_name)
    trace = None
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
                    image_uri, mime_type = handle_file_upload(file, vector_name)
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


def handle_file_upload(file, vector_name):
    try:
        file.save(file.filename)
        image_uri = add_file_to_gcs(file.filename, vector_name)
        os.remove(file.filename)  # Clean up the saved file
        return image_uri, file.mimetype
    except Exception as e:
        raise Exception(f'File upload failed: {str(e)}')