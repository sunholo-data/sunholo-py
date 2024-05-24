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

from ...agents import extract_chat_history, handle_special_commands
from ...qna.parsers import parse_output
from ...streaming import start_streaming_chat
from ...archive import archive_qa
from ...logging import log
from ...utils.config import load_config

try:
    from langfuse import Langfuse
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
        prep = prep_vac(request, vector_name)
        trace = prep["trace"]
        span = prep["span"]
        command_response = prep["command_response"]
        vac_config = prep["vac_config"]
        all_input = prep["all_input"]

        if command_response:
            return jsonify(command_response)

        log.info(f'Streaming data with stream_wait_time: {all_input["stream_wait_time"]} and stream_timeout: {all_input["stream_timeout"]}')
        def generate_response_content():
            if span:
                generation = span.generation(
                    name="start_streaming_chat",
                    metadata=vac_config,
                    input = all_input,
                    completion_start_time=datetime.datetime.now,
                    model=vac_config.get("model") or vac_config.get("llm")
                )
            chunks = ""
            for chunk in start_streaming_chat(user_input=all_input["user_input"],
                                              vector_name=vector_name,
                                              qna_func=stream_interpreter,
                                              chat_history=all_input["chat_history"],
                                              wait_time=all_input["stream_wait_time"],
                                              timeout=all_input["stream_timeout"],
                                              #kwargs
                                              message_author=all_input["message_author"]
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
                    yield f"###JSON_START###{json.dumps(chunk)}###JSON_END###"
  
                    return
                else:
                    # Otherwise, we yield the plain text chunks as they come in.
                    if chunk:
                        chunks += chunk
                        
                    yield chunk
            
            if trace:
                generation.end(output=chunks)
                span.end(output=chunks)
                trace.update(output=chunks)

        # Here, the generator function will handle streaming the content to the client.
        response = Response(generate_response_content(), content_type='text/plain; charset=utf-8')
        response.headers['Transfer-Encoding'] = 'chunked'  
        
        if langfuse:
            langfuse.flush()  

        return response

    @app.route('/vac/<vector_name>', methods=['POST'])
    def process_qna(vector_name):
        prep = prep_vac(request, vector_name)
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
            bot_output = vac_interpreter(
                user_input=all_input["all_input"],
                vector_name=vector_name,
                chat_history=all_input["chat_history"],
                message_author=all_input["message_author"]
            )
            if generation:
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
        name = f"/vac/{vector_name}",
        user_id = user_id,
        session_id = session_id,
        tags = tags,
        release = f"sunholo-v{package_version}"
    )

def prep_vac(request, vector_name):
    trace = create_langfuse_trace(request, vector_name)
    data = request.get_json()
    log.info(f"vac/{vector_name} got data: {data}")
    config, _ = load_config("config/llm_config.yaml")
    vac_configs = config.get("vac")
    if vac_configs:
        vac_config = vac_configs[vector_name]

    if trace:
        trace.update(input=data, metadata=vac_config)

    user_input = data['user_input'].strip()
    message_author = data.get('message_author', None)
    stream_wait_time = data.get('stream_wait_time', 7)
    stream_timeout = data.get('stream_timeout', 120)

    paired_messages = extract_chat_history(data.get('chat_history', None))
    all_input = {'user_input': user_input, 
                 'vector_name': vector_name, 
                 'chat_history': paired_messages, 
                 'message_author': message_author,
                 'stream_wait_time': stream_wait_time,
                 'stream_timeout':stream_timeout},

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