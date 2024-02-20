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
from threading import Thread, Event
from queue import Queue
import json
import time
import asyncio

from .content_buffer import ContentBuffer, BufferStreamingStdOutCallbackHandler

from ..qna.parsers import parse_output

from ..logging import setup_logging
from ..utils import load_config_key

from .langserve import parse_langserve_token, parse_langserve_token_async

logging = setup_logging()

def start_streaming_chat(question, 
                         vector_name,
                         qna_func,
                         chat_history=[],
                         wait_time=2,
                         timeout=120, # Timeout in seconds (2 minutes)
                         **kwargs): 

    # Immediately yield to indicate the process has started.
    yield "Thinking...\n"
    logging.info(f"Streaming chat with wait time {wait_time} seconds and timeout {timeout} seconds and kwargs {kwargs}")
    # Initialize the chat
    content_buffer = ContentBuffer()
    chat_callback_handler = BufferStreamingStdOutCallbackHandler(content_buffer=content_buffer, tokens=".!?\n")

    result_queue = Queue()
    exception_queue = Queue()  # Queue for exceptions
    stop_event = Event()

    def start_chat(stop_event, result_queue, exception_queue):
        # autogen_qna(user_input, vector_name, chat_history=None, message_author=None):
        try:
            final_result = qna_func(question, vector_name, chat_history, callback=chat_callback_handler, **kwargs)
            result_queue.put(final_result)
        except Exception as e:
            exception_queue.put(e)


    chat_thread = Thread(target=start_chat, args=(stop_event, result_queue, exception_queue))
    chat_thread.start()

    start = time.time()
    first_start = start
    while not chat_callback_handler.stream_finished.is_set() and not stop_event.is_set():

        time.sleep(wait_time) # Wait for x seconds
        logging.info(f"heartbeat - {round(time.time() - start, 2)} seconds")
        # Check for exceptions and raise if any
        while not exception_queue.empty():
            raise exception_queue.get()
        
        content_to_send = content_buffer.read()

        if content_to_send:
            logging.info(f"==\n{content_to_send}")
            yield content_to_send
            content_buffer.clear()
            start = time.time() # reset timeout
        else:
            if time.time() - first_start < wait_time:
                # If the initial wait period hasn't passed yet, keep sending "..."
                yield "..."
            else:
                logging.info("No content to send")

        elapsed_time = time.time() - start
        if elapsed_time > timeout: # If the elapsed time exceeds the timeout
            logging.warning(f"Content production has timed out after {timeout} secs")
            break
    else:
        logging.info(f"Stream has ended after {round(time.time() - first_start, 2)} seconds")
        logging.info("Sending final full message plus sources...")
        
    
    # if  you need it to stop it elsewhere use 
    # stop_event.set()
    content_to_send = content_buffer.read()
    if content_to_send:
        logging.info(f"==\n{content_to_send}")
        yield content_to_send
        content_buffer.clear()

    # Stop the stream thread
    chat_thread.join()

    # the json object with full response in 'answer' and the 'sources' array
    final_result = result_queue.get()

    # parses out source_documents if not present etc.
    yield parse_output(final_result)

async def start_streaming_chat_async(question, vector_name, qna_func, chat_history=[], wait_time=2, timeout=120, **kwargs): 
    # Indicate process start
    yield "Thinking...\n"
    logging.info(f"Streaming chat with wait time {wait_time} seconds and timeout {timeout} seconds and kwargs {kwargs}")

    content_buffer = ContentBuffer()
    chat_callback_handler = BufferStreamingStdOutCallbackHandler(content_buffer=content_buffer, tokens=".!?\n")

    result_queue = Queue()
    exception_queue = Queue()
    stop_event = Event()

    def start_chat():
        try:
            final_result = qna_func(question, vector_name, chat_history, callback=chat_callback_handler, **kwargs)
            result_queue.put(final_result)
        except Exception as e:
            exception_queue.put(e)

    chat_thread = Thread(target=start_chat)
    chat_thread.start()

    start = time.time()

    while not chat_callback_handler.stream_finished.is_set() and not stop_event.is_set():
        await asyncio.sleep(wait_time)  # Use asyncio.sleep for async compatibility
        logging.info(f"heartbeat - {round(time.time() - start, 2)} seconds")
        
        while not exception_queue.empty():
            exception = exception_queue.get_nowait()
            raise exception

        content_to_send = content_buffer.read()
        if content_to_send:
            logging.info(f"==\n{content_to_send}")
            yield content_to_send
            content_buffer.clear()
            start = time.time()
        else:
            if time.time() - start > timeout:
                logging.warning(f"Content production has timed out after {timeout} seconds")
                break

    stop_event.set()
    chat_thread.join()

    # Handle final result
    if not result_queue.empty():
        final_result = result_queue.get()
        # Ensure parse_output is called outside of the async generator context if needed
        parsed_final_result = parse_output(final_result)  # Assuming parse_output can handle final_result structure
        if 'answer' in parsed_final_result:  # Yield final structured result if needed
            yield f"###JSON_START###{json.dumps(parsed_final_result)}###JSON_END###"




def generate_proxy_stream(stream_to_f, user_input, vector_name, chat_history, generate_f_output, **kwargs):
    agent = load_config_key("agent", vector_name=vector_name, filename="config/llm_config.yaml")
    agent_type = load_config_key("agent_type", vector_name=vector_name, filename="config/llm_config.yaml")

    def generate():
        json_buffer = ""
        inside_json = False

        for streaming_content in stream_to_f(user_input, vector_name, chat_history, stream=True, **kwargs):
            json_buffer, inside_json, processed_output = process_streaming_content(streaming_content, generate_f_output, json_buffer, inside_json)
            for output in processed_output:
                if agent == "langserve" or agent_type == "langserve":
                    for parsed_output in parse_langserve_token(output):
                        yield parsed_output
                else:
                    yield output

    return generate



async def generate_proxy_stream_async(stream_to_f, user_input, vector_name, chat_history, generate_f_output, **kwargs):
    agent = load_config_key("agent", vector_name=vector_name, filename="config/llm_config.yaml")
    agent_type = load_config_key("agent_type", vector_name=vector_name, filename="config/llm_config.yaml")

    async def generate():
        json_buffer = ""
        inside_json = False

        async for streaming_content in stream_to_f(user_input, vector_name, chat_history, stream=True, **kwargs):
            json_buffer, inside_json, processed_output = process_streaming_content(streaming_content, generate_f_output, json_buffer, inside_json)
            for output in processed_output:
                if agent == "langserve" or agent_type == "langserve":
                    async for parsed_output in parse_langserve_token_async(output):
                        yield parsed_output
                else:
                    yield output

    return generate


def process_streaming_content(streaming_content, generate_f_output, json_buffer, inside_json):
    processed_outputs = []  # List to hold all processed outputs

    if isinstance(streaming_content, str):
        content_str = streaming_content

        # Handle string content
        if content_str.startswith('###JSON_START###'):
            logging.warning('Streaming content was a string with ###JSON_START###')
        else:
            logging.info(f'Streaming got a string we return directly: {content_str}')
            processed_outputs.append(content_str)
    else:
        # Decode if it's a bytes object
        content_str = streaming_content.decode('utf-8')

    logging.info(f'Content_str: {content_str}')

    # JSON processing logic
    while '###JSON_START###' in content_str:
        if '###JSON_END###' in content_str:
            start_index = content_str.index('###JSON_START###') + len('###JSON_START###')
            end_index = content_str.index('###JSON_END###')
            json_buffer = content_str[start_index:end_index]

            try:
                json_content = json.loads(json_buffer)
                parsed_output = generate_f_output(json_content)
                to_client = f'###JSON_START###{json.dumps(parsed_output)}###JSON_END###'
                logging.info(f"Streaming JSON to_client:\n{to_client}")
                 # Yielding the processed JSON
                processed_outputs.append(to_client.encode('utf-8'))
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}")

            content_str = content_str[end_index + len('###JSON_END###'):]
            json_buffer = ""

        else:
            start_index = content_str.index('###JSON_START###') + len('###JSON_START###')
            json_buffer = content_str[start_index:]
            inside_json = True
            break  # Exit while loop; rest will be handled by the next chunk

    if '###JSON_END###' in content_str and inside_json:
        end_index = content_str.index('###JSON_END###')
        json_buffer += content_str[:end_index]

        try:
            json_content = json.loads(json_buffer)
            parsed_output = generate_f_output(json_content)
            to_client = f'###JSON_START###{json.dumps(parsed_output)}###JSON_END###'
            logging.info(f"Streaming JSON to_client:\n{to_client}")
            # Yielding the processed JSON
            processed_outputs.append(to_client.encode('utf-8'))
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")

        content_str = content_str[end_index + len('###JSON_END###'):]
        json_buffer = ""
        inside_json = False

    if not inside_json and content_str:
        logging.info(f"Streaming to client:\n{content_str}")

        # Yielding non-JSON content
        processed_outputs.append(content_str.encode('utf-8'))
    
    return json_buffer, inside_json, processed_outputs
