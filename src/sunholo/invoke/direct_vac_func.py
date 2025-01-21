from ..custom_logging import log
from ..agents import send_to_qa, send_to_qa_async
from ..qna.parsers import parse_output
from ..streaming import generate_proxy_stream
from ..utils import ConfigManager
from ..utils.api_key import has_multivac_api_key
import asyncio
from threading import Thread

def direct_vac(vac_input: dict, vac_name: str, chat_history=None):
    """
    This lets VACs call other VAC Q&A endpoints within their code
    """

    log.info(f"Invoking VAC Q&A endpoints for {vac_name}")

    if 'user_input' not in vac_input:
        raise ValueError(f'vac_input must contain at least "user_input" key - got {vac_input}')

    global_config = ConfigManager('global')
    config = ConfigManager(vac_name)

    agent_name = config.vacConfig('agent')
    agent_url = config.vacConfig("agent_url")

    if agent_url:
        log.info("Found agent_url within vacConfig: {agent_url}")
    # via public cloud endpoints - assumes no gcloud auth
    override_endpoint = None
    if has_multivac_api_key():
        print("Found MULTIVAC_API_KEY")
        gcp_config = global_config.vacConfig("gcp_config")
        endpoints_base_url = gcp_config.get("endpoints_base_url")
        if not endpoints_base_url:
            raise ValueError("MULTIVAC_API_KEY env var is set but no config.gcp_config.endpoints_base_url can be found")

        override_endpoint = f"{endpoints_base_url}/v1/{agent_name}"

    override_endpoint = agent_url or override_endpoint

    print(f"Using {override_endpoint=}")
    
    # Prepare the kwargs for send_to_qa by copying vac_input and adding more values
    qa_kwargs = vac_input.copy()
    if not chat_history:
        chat_history = []

    # Add additional arguments
    qa_kwargs.update({
        'vector_name': vac_name,
        'chat_history': chat_history,
        'image_url': vac_input.get('image_url') or vac_input.get('image_uri'),
        'override_endpoint': override_endpoint,
        'message_source': "sunholo.invoke_vac_qa.invoke",
        'stream': False,
        'configurable': {
            "vector_name": vac_name,
        },
    })

    log.info(f'Batch invoke_vac_qa {vac_name} with {qa_kwargs=}')

    vac_response = send_to_qa(**qa_kwargs)
        
    # ensures {'answer': answer}
    answer = parse_output(vac_response)
    chat_history.append({"name": "Human", "content": vac_input})
    chat_history.append({"name": "AI", "content": answer})
    answer["chat_history"] = chat_history
    
    return answer

async def async_direct_vac(vac_input: dict, vac_name: str, chat_history=None):
    """
    Asynchronous version of direct_vac using send_to_qa_async.
    Allows VACs to call other VAC Q&A endpoints without blocking the event loop.
    """
    log.info(f"Invoking VAC Q&A endpoints for {vac_name}")

    if 'user_input' not in vac_input:
        raise ValueError(f'vac_input must contain at least "user_input" key - got {vac_input}')

    global_config = ConfigManager('global')
    config = ConfigManager(vac_name)

    agent_name = config.vacConfig('agent')
    agent_url = config.vacConfig("agent_url")

    if agent_url:
        log.info(f"Found agent_url within vacConfig: {agent_url}")

    # Via public cloud endpoints - assumes no gcloud auth
    override_endpoint = None
    if has_multivac_api_key():
        print("Found MULTIVAC_API_KEY")
        gcp_config = global_config.vacConfig("gcp_config")
        endpoints_base_url = gcp_config.get("endpoints_base_url")
        if not endpoints_base_url:
            raise ValueError("MULTIVAC_API_KEY env var is set but no config.gcp_config.endpoints_base_url can be found")

        override_endpoint = f"{endpoints_base_url}/v1/{agent_name}"

    override_endpoint = agent_url or override_endpoint

    print(f"Using override_endpoint={override_endpoint}")

    # Prepare the kwargs for send_to_qa_async by copying vac_input and adding more values
    qa_kwargs = vac_input.copy()

    if not chat_history:
        chat_history = []

    # Add additional arguments
    qa_kwargs.update({
        'vector_name': vac_name,
        'chat_history': chat_history,
        'image_url': vac_input.get('image_url') or vac_input.get('image_uri'),
        'override_endpoint': override_endpoint,
        'message_source': "sunholo.invoke_vac_qa.invoke",
        'stream': False,
        'configurable': {
            "vector_name": vac_name,
        },
    })

    log.info(f'Batch invoke_vac_qa {vac_name} with qa_kwargs={qa_kwargs}')

    # Call send_to_qa_async directly
    vac_response_generator = send_to_qa_async(**qa_kwargs)

    # Since send_to_qa_async returns an async generator, we can get the response
    vac_response = None
    async for response in vac_response_generator:
        vac_response = response  # Since stream=False, we expect only one response
        break

    # Call parse_output synchronously (since it's non-blocking)
    answer = parse_output(vac_response)

    chat_history.append({"name": "Human", "content": vac_input})
    chat_history.append({"name": "AI", "content": answer})
    answer["chat_history"] = chat_history

    return answer

def direct_vac_stream(vac_input: dict, vac_name: str, chat_history=None):

    if 'user_input' not in vac_input:
        raise ValueError('vac_input must contain at least "user_input" key - got {vac_input}')

    user_id = vac_input.get('user_id')
    session_id = vac_input.get('session_id')
    image_uri = vac_input.get('image_url') or vac_input.get('image_uri')

    if not chat_history:
        chat_history = []
    
    log.info(f"Streaming invoke_vac_qa with {vac_input=}")
    def stream_response():
        generate = generate_proxy_stream(
                send_to_qa,
                vac_input["user_input"],
                vector_name=vac_name,
                chat_history=chat_history,
                generate_f_output=lambda x: x,  # Replace with actual processing function
                stream_wait_time=0.5,
                stream_timeout=120,
                message_author=user_id,
                #TODO: populate these
                image_url=image_uri,
                source_filters=None,
                search_kwargs=None,
                private_docs=None,
                whole_document=False,
                source_filters_and_or=False,
                # system kwargs
                configurable={
                    "vector_name": vac_name,
                },
                user_id=user_id,
                session_id=session_id, 
                message_source="sunholo.invoke_vac_qa.stream"
        )
        for part in generate():
            yield part

    answer = ""

    for token in stream_response():
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            yield token
        if isinstance(token, dict):
            # ?
            pass
        elif isinstance(token, str):
            answer += token

    if answer:
        chat_history.append({"name": "Human", "content": vac_input})
        chat_history.append({"name": "AI", "content": answer})

    return chat_history



async def async_direct_vac_stream(vac_input: dict, vac_name: str, chat_history=None):
    """
    Asynchronous version of direct_vac_stream.
    Streams responses from VAC Q&A endpoints without blocking the event loop.
    """
    if 'user_input' not in vac_input:
        raise ValueError(f'vac_input must contain at least "user_input" key - got {vac_input}')

    user_id = vac_input.get('user_id')
    session_id = vac_input.get('session_id')
    image_uri = vac_input.get('image_url') or vac_input.get('image_uri')

    log.info(f"Streaming invoke_vac_qa with vac_input={vac_input}")
    if not chat_history:
        chat_history = []

    def sync_stream_response():
        generate = generate_proxy_stream(
            send_to_qa,
            vac_input["user_input"],
            vector_name=vac_name,
            chat_history=chat_history or [],
            generate_f_output=lambda x: x,  # Replace with actual processing function
            stream_wait_time=0.5,
            stream_timeout=120,
            message_author=user_id,
            # TODO: populate these
            image_url=image_uri,
            source_filters=None,
            search_kwargs=None,
            private_docs=None,
            whole_document=False,
            source_filters_and_or=False,
            # system kwargs
            configurable={
                "vector_name": vac_name,
            },
            user_id=user_id,
            session_id=session_id,
            message_source="sunholo.invoke_vac_qa.stream"
        )
        for part in generate():
            yield part

    async def async_stream_response():
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def run_sync_gen():
            try:
                for item in sync_stream_response():
                    loop.call_soon_threadsafe(queue.put_nowait, item)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # Sentinel

        thread = Thread(target=run_sync_gen)
        thread.start()

        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

        thread.join()

    answer = ""

    async for token in async_stream_response():
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            yield token
        if isinstance(token, dict):
            # Process dict token if necessary
            pass
        elif isinstance(token, str):
            answer += token

    if answer:
        chat_history.append({"name": "Human", "content": vac_input})
        chat_history.append({"name": "AI", "content": answer})

    yield chat_history