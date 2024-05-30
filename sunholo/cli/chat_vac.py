from ..agents import send_to_qa_async
from ..streaming import generate_proxy_stream_async, generate_proxy_stream
from ..utils.user_ids import generate_uuid_from_gcloud_user

from .run_proxy import load_proxies, start_proxy

import uuid

def get_service_url(service_name):
    proxies = load_proxies()
    if service_name in proxies:
        port = proxies[service_name]['port']
        return f"http://127.0.0.1:{port}"
    else:
        print(f"No proxy found running for service: {service_name} - attempting to connect")
        return start_proxy(service_name)

async def stream_chat_session(service_name, chat_history):

    service_url = get_service_url(service_name)
    user_id = generate_uuid_from_gcloud_user()
    while True:
        session_id = str(uuid.uuid4())
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat session.")
            break

        chat_history.append({"role": "user", "content": user_input})

        

        async def stream_response():
            generate = await generate_proxy_stream_async(
                send_to_qa_async,
                user_input,
                vector_name=service_name,
                chat_history=chat_history,
                generate_f_output=lambda x: x,  # Replace with actual processing function
                stream_wait_time=0.5,
                stream_timeout=120,
                message_author=user_id,
                #TODO: populate these
                image_url=None,
                source_filters=None,
                search_kwargs=None,
                private_docs=None,
                whole_document=False,
                source_filters_and_or=False,
                # system kwargs
                configurable={
                    "vector_name": service_name,
                },
                user_id=user_id,
                session_id=session_id, 
                message_source="cli",
                override_endpoint=service_url
            )
            async for part in generate():
                yield part

        print("Assistant: ", end='', flush=True)
        async for token in stream_response():
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            print(token, end='', flush=True)

        chat_history.append({"role": "assistant", "content": token})
        print()  # For new line after streaming ends

async def headless_mode(service_name, user_input, chat_history=None):
    chat_history = chat_history or []
    chat_history.append({"role": "user", "content": user_input})
    service_url = get_service_url(service_name)
    user_id = generate_uuid_from_gcloud_user()
    session_id = str(uuid.uuid4())

    async def stream_response():
        generate = await generate_proxy_stream_async(
                send_to_qa_async,
                user_input,
                vector_name=service_name,
                chat_history=chat_history,
                generate_f_output=lambda x: x,  # Replace with actual processing function
                stream_wait_time=0.5,
                stream_timeout=120,
                message_author=user_id,
                #TODO: populate these
                image_url=None,
                source_filters=None,
                search_kwargs=None,
                private_docs=None,
                whole_document=False,
                source_filters_and_or=False,
                # system kwargs
                configurable={
                    "vector_name": service_name,
                },
                user_id=user_id,
                session_id=session_id, 
                message_source="cli",
                override_endpoint=service_url
        )
        async for part in generate():
            yield part

    print("Assistant: ", end='', flush=True)
    async for token in stream_response():
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        print(token, end='', flush=True)

    chat_history.append({"role": "assistant", "content": token})
    print()  # For new line after streaming ends


def vac_command(args):
    try:
        service_url = get_service_url(args.service_name)
    except ValueError as e:
        print(e)
        return

    if args.headless:
        headless_mode(service_url, args.user_input, args.chat_history)
    else:
        stream_chat_session(service_url)

def setup_vac_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'vac' command.

    Args:
        subparsers: The subparsers object from argparse.ArgumentParser().
    """
    vac_parser = subparsers.add_parser('vac', help='Interact with the VAC service.')
    vac_parser.add_argument('service_name', help='Name of the VAC service.')
    vac_parser.add_argument('user_input', help='User input for the VAC service.', nargs='?', default=None)
    vac_parser.add_argument('--headless', action='store_true', help='Run in headless mode.')
    vac_parser.add_argument('--chat_history', help='Chat history for headless mode (as JSON string).', default=None)
    vac_parser.set_defaults(func=vac_command)
