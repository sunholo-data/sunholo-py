from ..agents import send_to_qa, handle_special_commands
from ..streaming import generate_proxy_stream, can_agent_stream
from ..utils.user_ids import generate_user_id
from ..utils.config import load_config_key
from ..logging import log
from ..qna.parsers import parse_output
from .run_proxy import clean_proxy_list, start_proxy, stop_proxy

import uuid
import sys
import subprocess
import json
import requests
from pathlib import Path

from rich import print
from .sun_rich import console

from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.table import Table


def get_service_url(vac_name, project, region, no_config=False):

    if no_config:
        agent_name = vac_name
    else:
        agent_name = load_config_key("agent", vac_name, kind="vacConfig")

    proxies = clean_proxy_list()
    if agent_name in proxies:
        port = proxies[agent_name]['port']
        url = f"http://127.0.0.1:{port}"
    else:
        if agent_name:
            console.print(f"No proxy found running for service: [bold orange]'{agent_name}'[/bold orange] required for [bold orange]{vac_name}[/bold orange] - attempting to connect")
            url = start_proxy(agent_name, region, project)
        else:
            console.print(f"No config for [bold orange]'{vac_name}'[/bold orange] - can't start proxy")
            sys.exit(1)

    return url

def stream_chat_session(service_url, service_name, stream=True):

    user_id = generate_user_id()
    chat_history = []
    while True:
        session_id = str(uuid.uuid4())
        user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        if user_input.lower() in ["exit", "quit"]:
            console.print("[bold red]Exiting chat session.[/bold red]")
            break

        special_reply = handle_special_commands(
            user_input, 
            vector_name=service_name,
            chat_history=chat_history)

        if special_reply:
             console.print(f"[bold yellow]{service_name}:[/bold yellow] {special_reply}", end='\n')
             continue     
        
        if not stream:
            vac_response = send_to_qa(user_input,
                vector_name=service_name,
                chat_history=chat_history,
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
                override_endpoint=service_url)
            
            # ensures {'answer': answer}
            answer = parse_output(vac_response)
            
            console.print(f"[bold yellow]{service_name}:[/bold yellow] {answer.get('answer')}", end='\n')
        else:

            def stream_response():
                generate = generate_proxy_stream(
                    send_to_qa,
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
                for part in generate():
                    yield part

            response_started = False
            vac_response = ""

            # point or star?
            with console.status("[bold orange]Thinking...[/bold orange]", spinner="star") as status:
                for token in stream_response():
                    if not response_started:
                        status.stop()
                        console.print(f"[bold yellow]{service_name}:[/bold yellow] ", end='')
                        response_started = True

                    if isinstance(token, bytes):
                        token = token.decode('utf-8')
                    console.print(token, end='')
                    vac_response += token

            response_started = False

        chat_history.append({"name": "Human", "content": user_input})
        chat_history.append({"name": "AI", "content": vac_response})
        
        console.print()
        console.rule()

def headless_mode(service_url, service_name, user_input, chat_history=None, stream=True):
    chat_history = chat_history or []

    user_id = generate_user_id()
    session_id = str(uuid.uuid4())

    def stream_response():
        generate = generate_proxy_stream(
                send_to_qa,
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
        for part in generate():
            yield part

    vac_response = ""

    for token in stream_response():
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        print(token, end='', flush=True)
        vac_response += token

    if vac_response:
        chat_history.append({"name": "Human", "content": user_input})
        chat_history.append({"name": "AI", "content": vac_response})
    print()  # For new line after streaming ends

    return chat_history

def resolve_service_url(args, no_config=False):
    """
    no_config: some VACs do not have an entry in the config file e.g. chunker, embedder etc.
    """
    if args.url_override:

        return args.url_override

    if args.no_proxy:
        agent_url = load_config_key("agent_url", args.vac_name, "vacConfig")
        if agent_url:
            console.print("Found agent_url within vacConfig: {agent_url}")
        
        service_url = agent_url or get_cloud_run_service_url(args.project, args.region, args.vac_name)
        console.print(f"No proxy, connecting directly to {service_url}")
    else:
        try:
            service_url = get_service_url(args.vac_name, args.project, args.region, no_config=no_config)
        except ValueError as e:
            console.print(f"[bold red]ERROR: Could not start {args.vac_name} proxy URL: {str(e)}[/bold red]")
            sys.exit(1)
    
    return service_url

def vac_command(args):

    if args.action == 'list':

        list_cloud_run_services(args.project, args.region)

        return
    
    elif args.action == 'get-url':
        service_url = resolve_service_url(args)
        console.print(service_url)

        return
    
    elif args.action == 'chat':
        service_url = resolve_service_url(args)
        agent_name   = load_config_key("agent", args.vac_name, kind="vacConfig")

        streamer = can_agent_stream(agent_name)
        log.debug(f"streamer: {streamer}")
        if not streamer:
            console.print(f"Non streaming agent: {args.vac_name}")

        if args.headless:
            headless_mode(service_url, args.vac_name, args.user_input, args.chat_history, stream=streamer)
        else:
            display_name = load_config_key("display_name", vector_name=args.vac_name,  kind="vacConfig")
            description  = load_config_key("description", vector_name=args.vac_name, kind="vacConfig")
            endpoints_config = load_config_key(agent_name, "dummy_value", kind="agentConfig")

            display_endpoints = ' '.join(f"{key}: {value}" for key, value in endpoints_config.items())
            display_endpoints = display_endpoints.replace("{stem}", service_url).replace("{vector_name}", args.vac_name)

            if agent_name == "langserve":
                subtitle = f"{service_url}/{args.vac_name}/playground/"
            else:
                subtitle = display_endpoints

            print(
                Panel(description or "Starting VAC chat session", 
                    title=display_name or args.vac_name,
                    subtitle=subtitle)
                    )

            stream_chat_session(service_url, args.vac_name, stream=streamer)
        
        stop_proxy(agent_name, stop_local=False)

    elif args.action == 'invoke':
        service_url = resolve_service_url(args, no_config=True)

        invoke_vac(service_url, args.data, is_file=args.is_file)

def invoke_vac(service_url, data, vector_name=None, metadata=None, is_file=False):
    try:
        if is_file:
            console.print("Uploading file to chunker...")
            # Handle file upload
            if not isinstance(data, Path) or not data.is_file():
                raise ValueError("For file uploads, 'data' must be a Path object pointing to a valid file.")
            
            files = {
                'file': (data.name, open(data, 'rb')),
            }
            form_data = {
                'vector_name': vector_name,
                'metadata': json.dumps(metadata) if metadata else '',
            }

            response = requests.post(service_url, files=files, data=form_data)
        else:
            console.print("Uploading JSON to chunker...")
            try:
                if isinstance(data, dict):
                    json_data = data
                else:
                    json_data = json.loads(data)
            except json.JSONDecodeError as err:
                console.print(f"[bold red]ERROR: invalid JSON: {str(err)} [/bold red]")
                sys.exit(1)
            except Exception as err:
                console.print(f"[bold red]ERROR: could not parse JSON: {str(err)} [/bold red]")
                sys.exit(1)

            log.debug(f"Sending data: {data} or json_data: {json.dumps(json_data)}")
            # Handle JSON data
            headers = {"Content-Type": "application/json"}
            response = requests.post(service_url, headers=headers, data=json.dumps(json_data))

        response.raise_for_status()

        the_data = response.json()
        console.print(the_data)

        return the_data
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]ERROR: Failed to invoke VAC: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]ERROR: An unexpected error occurred: {e}[/bold red]")


def list_cloud_run_services(project, region):
    """
    Lists all Cloud Run services the user has access to in a specific project and region.

    Args:
        project (str): The GCP project ID.
        region (str): The region of the Cloud Run services.
    """

        # point or star?
    with console.status("[bold orange]Listing Cloud Run Services[/bold orange]", spinner="star") as status:
        try:
            result = subprocess.run(
                ["gcloud", "run", "services", "list", "--project", project, "--region", region, "--format=json"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
            )
            if result.returncode != 0:
                status.stop()
                console.print(f"[bold red]ERROR: Unable to list Cloud Run services: {result.stderr.decode()}[/bold red]")
                return

            services = json.loads(result.stdout.decode())
            if not services:
                status.stop()
                console.print("[bold red]No Cloud Run services found.[/bold red]")
                return

            proxies = clean_proxy_list()
            status.stop()

            table = Table(title="VAC Cloud Run Services")
            table.add_column("Service Name")
            table.add_column("Region")
            table.add_column("URL")
            table.add_column("Proxied")
            table.add_column("Port")
            
            for service in services:
                service_name = service['metadata']['name']
                service_url = service['status']['url']
                if service_name in proxies:
                    proxied = "Yes"
                    proxy_port = proxies[service_name]['port']
                else:
                    proxied = "No"
                    proxy_port = "-"
                table.add_row(service_name, region, service_url, proxied, str(proxy_port))

            console.print(table)
        except Exception as e:
            status.stop()
            console.print(f"[bold red]ERROR: An unexpected error occurred: {e}[/bold red]")


def get_cloud_run_service_url(project, region, service_name):
    """
    Retrieves the URL of a specific Cloud Run service in a given project and region.

    Args:
        project (str): The GCP project ID.
        region (str): The region of the Cloud Run service.
        service_name (str): The name of the Cloud Run service.

    Returns:
        str: The URL of the Cloud Run service, or an error message if not found.
    """
    try:
        result = subprocess.run(
            ["gcloud", "run", "services", "describe", service_name, "--project", project, "--region", region, "--format=json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
        )
        if result.returncode != 0:
            console.print(f"[bold red]ERROR: Unable to get Cloud Run service URL: {result.stderr.decode()}[/bold red]")
            return None

        service = json.loads(result.stdout.decode())
        service_url = service['status']['url']
        return service_url
    except Exception as e:
        console.print(f"[bold red]ERROR: An unexpected error occurred: {e}[/bold red]")
        return None

    

def setup_vac_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'vac' command.

    Args:
        subparsers: The subparsers object from argparse.ArgumentParser().
    """
    vac_parser = subparsers.add_parser('vac', help='Interact with deployed VAC services.')
    vac_parser.add_argument('--url_override', help='Override the VAC service URL.')
    vac_parser.add_argument('--no-proxy', action='store_true', help='Do not use the proxy and connect directly to the VAC service.')
    vac_subparsers = vac_parser.add_subparsers(dest='action', help='VAC subcommands')

    # Subcommand for listing VAC services
    list_parser = vac_subparsers.add_parser('list', help='List all VAC services.')

    # Subcommand for getting the URL of a specific VAC service
    get_url_parser = vac_subparsers.add_parser('get-url', help='Get the URL of a specific VAC service.')
    get_url_parser.add_argument('vac_name', help='Name of the VAC service.')

    # Subcommand for interacting with a VAC service
    chat_parser = vac_subparsers.add_parser('chat', help='Interact with a VAC service.')
    chat_parser.add_argument('vac_name', help='Name of the VAC service.')
    chat_parser.add_argument('user_input', help='User input for the VAC service when in headless mode.', nargs='?', default=None)
    chat_parser.add_argument('--headless', action='store_true', help='Run in headless mode.')
    chat_parser.add_argument('--chat_history', help='Chat history for headless mode (as JSON string).', default=None)

    # Subcommand for invoking a VAC service directly
    invoke_parser = vac_subparsers.add_parser('invoke', help='Invoke a VAC service directly with custom data.')
    invoke_parser.add_argument('vac_name', help='Name of the VAC service.')
    invoke_parser.add_argument('data', help='Data to send to the VAC service (as JSON string).')
    invoke_parser.add_argument('--is-file', action='store_true', help='Indicate if the data argument is a file path')

    vac_parser.set_defaults(func=vac_command)
