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

from ...agents import extract_chat_history, handle_special_commands
from ...qna.parsers import parse_output
from ...streaming import start_streaming_chat
from ...archive import archive_qa
from ...logging import log
from ...utils.config import load_config

try:
    from langfuse import Langfuse, langfuse_context
    langfuse = Langfuse()
except ImportError as err:
    print(f"No langfuse installed for agents.flask.register_qna_routes, install via `pip install sunholo[http]` - {str(err)}")
    langfuse = None
 
try:
    from flask import request, jsonify, Response
except ImportError:
    print("No flask installed for agents.flask.register_qna_routes, install via `pip install sunholo[http]`")

def register_qna_routes(app, stream_interpreter, vac_interpreter):

    @app.route('/vac/streaming/<vector_name>', methods=['POST'])
    def stream_qa(vector_name):
        trace = create_langfuse_trace(request, vector_name)

        log.info(f"Calling /vac/streaming/{vector_name} - langfuse trace: {langfuse_context.get_current_trace_url()}")
        data = request.get_json()
        if trace:
            trace.update(input=data)

        user_input = data['user_input'].strip()  # Extract user input from the payload
        chat_history = data.get('chat_history', None)
        stream_wait_time = data.get('stream_wait_time', 7)
        stream_timeout = data.get('stream_timeout', 120)

        # kwargs for streaming extracted from the payload here
        message_author = data.get('message_author', None)

        paired_messages = extract_chat_history(chat_history)

        command_response = handle_special_commands(user_input, vector_name, paired_messages)
        if command_response is not None:
            if trace:
                trace.update(output=jsonify(command_response))

            return jsonify(command_response)

        log.info(f'Streaming data with stream_wait_time: {stream_wait_time} and stream_timeout: {stream_timeout}')
        def generate_response_content():
            config, _ = load_config("config/llm_config.yaml")
            vac_config = config[vector_name]
            model = vac_config.get("model") or vac_config.get("llm")
            
            if trace:
                generation = trace.generation(
                    name="VAC",
                    model=model,
                    metadata=vac_config,
                    input = {'user_input': user_input, 'vector_name': vector_name, 'chat_history': paired_messages, 'message_author': message_author},
                )
            chunks = ""
            for chunk in start_streaming_chat(user_input,
                                              vector_name=vector_name,
                                              qna_func=stream_interpreter,
                                              chat_history=paired_messages,
                                              wait_time=stream_wait_time,
                                              timeout=stream_timeout,
                                              #kwargs
                                              message_author=message_author
                                              ):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    # When we encounter the dictionary, we yield it as a JSON string
                    # and stop the generator.
                    archive_qa(chunk, vector_name)
                    if trace:
                        generation.end(
                            output=json.dumps(chunk)
                        )
                    yield f"###JSON_START###{json.dumps(chunk)}###JSON_END###"
  
                    return
                else:
                    # Otherwise, we yield the plain text chunks as they come in.
                    chunks += chunk
                    yield chunk
            
            if trace:
                generation.end(
                    output=chunks
                )

        # Here, the generator function will handle streaming the content to the client.
        response = Response(generate_response_content(), content_type='text/plain; charset=utf-8')
        response.headers['Transfer-Encoding'] = 'chunked'  
        
        if langfuse:
            langfuse.flush()  

        return response

    @app.route('/vac/<vector_name>', methods=['POST'])
    def process_qna(vector_name):
        trace = create_langfuse_trace(request, vector_name)
        data = request.get_json()
        log.info(f"qna/{vector_name} got data: {data}")

        if trace:
            trace.update(input=data)

        user_input = data['user_input'].strip()

        message_author = data.get('message_author', None)

        paired_messages = extract_chat_history(data.get('chat_history', None))

        command_response = handle_special_commands(user_input, vector_name, paired_messages)
        if command_response is not None:
            if trace:
                trace.update(output=jsonify(command_response))

            return jsonify(command_response)

        try:
            config, _ = load_config("config/llm_config.yaml")
            vac_config = config[vector_name]
            model = vac_config.get("model") or vac_config.get("llm")
            
            if trace:
                generation = trace.generation(
                    name="VAC",
                    model=model,
                    metadata=vac_config,
                    input = {'user_input': user_input, 'vector_name': vector_name, 'chat_history': paired_messages, 'message_author': message_author},
                )
            bot_output = vac_interpreter(user_input, vector_name, chat_history=paired_messages, message_author=message_author)
            # {"answer": "The answer", "source_documents": [{"page_content": "The page content", "metadata": "The metadata"}]}
            bot_output = parse_output(bot_output)
            archive_qa(bot_output, vector_name)
            log.info(f'==LLM Q:{user_input} - A:{bot_output}')

            if trace:
                generation.end(
                    output=jsonify(bot_output),
                )
        except Exception as err: 
            bot_output = {'answer': f'QNA_ERROR: An error occurred while processing /vac/{vector_name}: {str(err)} traceback: {traceback.format_exc()}'}
        
        if langfuse:
            langfuse.flush()

        return jsonify(bot_output)

    # Any other QNA related routes can be added here

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

    # can't import tags yet via CallbackHandler
    from importlib.metadata import version
    package_version = version('sunholo')
    tags = [f"sunholo-v{package_version}"]
    if message_source:
        tags.append(message_source)
    
    return langfuse.trace(
        name = f"/vac/streaming/{vector_name}",
        user_id = user_id,
        session_id = session_id,
        tags = tags,
        release = f"sunholo-v{package_version}"
    )