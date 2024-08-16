from ..custom_logging import log
from ..agents import send_to_qa
from ..qna.parsers import parse_output
from ..streaming import generate_proxy_stream
from ..utils import ConfigManager
from ..utils.api_key import has_multivac_api_key

def direct_vac(vac_input: dict, vac_name: str, chat_history=[]):
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

def direct_vac_stream(vac_input: dict, vac_name: str, chat_history=[]):

    if 'user_input' not in vac_input:
        raise ValueError('vac_input must contain at least "user_input" key - got {vac_input}')

    user_id = vac_input.get('user_id')
    session_id = vac_input.get('session_id')
    image_uri = vac_input.get('image_url') or vac_input.get('image_uri')
    
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