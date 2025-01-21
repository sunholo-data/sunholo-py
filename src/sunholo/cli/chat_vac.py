from ..agents import send_to_qa, handle_special_commands
from ..streaming import generate_proxy_stream, can_agent_stream
from ..utils.user_ids import generate_user_id
from ..utils import ConfigManager
from ..utils.api_key import has_multivac_api_key
from ..custom_logging import log
from ..qna.parsers import parse_output
from ..gcs.add_file import add_file_to_gcs
from .run_proxy import clean_proxy_list, start_proxy, stop_proxy
from ..invoke import invoke_vac
from ..utils.big_context import has_text_extension, merge_text_files, load_gitignore_patterns, build_file_tree
import tempfile

import uuid
import os
import sys
import subprocess
import json
from pathlib import Path

from rich import print
from .sun_rich import console

from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

def read_and_add_to_user_input(user_input):
    read_input = None

    path = user_input.split(" ", 1)[1] if " " in user_input else None
    if not path:
        console.print("[bold red]Please provide a valid file or folder path.[/bold red]")
        return None

    if os.path.isfile(path):
        if not has_text_extension(path):
            console.print("[bold red]Unsupported file type. Please provide a text file or preprocess to text, or use !upload (e.g. images) or `sunholo embed`.[/bold red]")
            return None

        try:
            with open(path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            read_input = file_content
            console.print(f"[bold yellow]File content from {path} read into user_input: [{len(read_input.split())}] words[/bold yellow]")
        except FileNotFoundError:
            console.print("[bold red]File not found. Please check the path and try again.[/bold red]")
            return None
        except IOError:
            console.print("[bold red]File could not be read. Please ensure it is a readable text file.[/bold red]")
            return None
    elif os.path.isdir(path):
        patterns = []
        gitignore_path = os.path.join(path, '.gitignore')
    
        if os.path.exists(gitignore_path):
            patterns = load_gitignore_patterns(gitignore_path)
    
        try:
            with tempfile.NamedTemporaryFile(delete=False, mode='w+', encoding='utf-8') as temp_file:
                temp_file_path = temp_file.name
                file_tree = merge_text_files(path, temp_file_path, patterns)
                console.print(f"[bold yellow]Contents of the folder '{path}' have been merged add added to input.[/bold yellow]")
                console.print("\n".join(file_tree))
                temp_file.seek(0)
                read_input = temp_file.read()
                console.print(f"[bold yellow]Total words: [{len(read_input.split())}] - watch out for high token costs! Use !clear_read to reset[/bold yellow]")
            os.remove(temp_file_path)  # Clean up the temporary file
        except Exception as e:
            console.print(f"[bold red]An error occurred while reading the folder: {str(e)}[/bold red]")
            return None
    else:
        console.print("[bold red]The provided path is neither a file nor a folder. Please check the path and try again.[/bold red]")
        return None
    
    return read_input

def get_service_url(vac_name, project, region, no_config=False):

    if no_config:
        agent_name = vac_name
    else:
        agent_name = ConfigManager(vac_name).vacConfig("agent")

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

def handle_file_upload(file, vector_name):
    if not Path(file).is_file():
        return None
    
    agent_name = ConfigManager(vector_name).vacConfig("agent")
    # vertex can't handle directories
    bucket_filepath = f"{vector_name}/uploads/{os.path.basename(file)}" if agent_name != "vertex-genai" else os.path.basename(file)

    file_url = add_file_to_gcs(file, 
                               vector_name=vector_name, 
                               metadata={"type": "cli"},
                               bucket_filepath=bucket_filepath)
    
    return file_url

def stream_chat_session(service_url, service_name, stream=True):

    user_id = generate_user_id()
    chat_history = []
    agent_name = ConfigManager(service_name).vacConfig("agent")
    file_reply = None
    read_file = None
    read_file_count = None
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

        if user_input.lower().startswith("!read"):
            read_file = read_and_add_to_user_input(user_input)
            if read_file:
                read_file_count = len(read_file.split())
            continue

        if user_input.lower().startswith("!ls"):
            items = os.listdir(os.getcwd())
            for item in items:
                console.print(item)
            continue

        if user_input.lower().startswith("!tree"):
            tree = build_file_tree(os.getcwd(), patterns=[])
            console.print(tree)
            continue

        if user_input.lower().startswith("!upload"):
            file_path = user_input.split(" ", 1)[1] if " " in user_input else None
            if not file_path:
                console.print("[bold red]Please provide a valid file path.[/bold red]")
                continue

            try:
                file_reply = handle_file_upload(file_path, vector_name=service_name)
                if not file_reply:
                    console.print("[bold red]Invalid file upload[/bold red]")
                    continue
                
                console.print(f"[bold yellow]{service_name}:[/bold yellow] Uploaded {file_path} to {file_reply} - image will be sent each reply until you issue '!clear_upload' ", end='\n')
            
            except FileNotFoundError:
                console.print("[bold red]File not found. Please check the path and try again.[/bold red]")

            # file_reply stays for each message from now on
            continue 

        if user_input.lower().startswith("!clear_upload"):
            console.print("[bold yellow]File upload path cleared.[/bold yellow]")
            file_path = None
            continue

        if user_input.lower().startswith("!clear_read"):
            console.print("[bold yellow]Read in file(s) cleared.[/bold yellow]")
            read_file = None
            read_file_count = None
            continue

        if user_input.lower().startswith("!"):
            console.print("[bold red]Could find no valid chat command for you, sorry[/bold red]")
            continue
        
        if read_file:
            user_input = f"<user added file>{read_file}</user added file>\n{user_input}"
        
        # guardrail
        if len(user_input)> 1000000:
            console.print("[bold red]Over 1 million characters in user_input, aborting as probably unintentional. Use API directly instead.[/bold red]")
            continue

        if not stream:
            vac_response = send_to_qa(user_input,
                vector_name=service_name,
                chat_history=chat_history,
                message_author=user_id,
                #TODO: populate these
                image_url=file_reply,
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
                    stream_timeout=120 if agent_name != "vertex-genai" else 1200,
                    message_author=user_id,
                    #TODO: populate these
                    image_url=file_reply,
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

            
            thinking = "[bold orange]Thinking...[/bold orange]"
            if file_reply:
                thinking = f"[bold orange]Thinking with upload {file_reply} - issue !clear_upload to remove...[/bold orange]"
            
            if read_file:
                thinking = f"{thinking} - [bold orange]additional [{read_file_count}] words added via !read_file contents - issue !clear_read to remove[/bold orange]"

            with console.status(thinking, spinner="star") as status:
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
        
        console.print(answer.get('answer'))
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

        answer = ""

        for token in stream_response():
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            print(token, end='', flush=True)
            if isinstance(token, dict):
                # ?
                pass
            elif isinstance(token, str):
                answer += token

    if answer:
        chat_history.append({"name": "Human", "content": user_input})
        chat_history.append({"name": "AI", "content": answer})
    print()  # For new line after streaming ends

    return chat_history

def resolve_service_url(args, no_config=False):
    """
    no_config: some VACs do not have an entry in the config file e.g. chunker, embedder etc.
    """
    if args.url_override:

        return args.url_override
    
    config = ConfigManager(args.vac_name)
    global_config = ConfigManager("global")

    agent_name = config.vacConfig("agent")
    agent_url = config.vacConfig("agent_url")

    if agent_url:
        console.print("Found agent_url within vacConfig: {agent_url}")
    
    # via public cloud endpoints - assumes no gcloud auth
    if has_multivac_api_key():
        log.debug("Found MULTIVAC_API_KEY")
        gcp_config = global_config.vacConfig("gcp_config")
        endpoints_base_url = gcp_config.get("endpoints_base_url")
        if not endpoints_base_url:
            console.print("[bold red]MULTIVAC_API_KEY env var is set but no config.gcp_config.endpoints_base_url can be found[/bold red]")
            sys.exit(1)

        return f"{endpoints_base_url}/v1/{agent_name}"

    # via direct access to agent url - requires gcloud auth access
    elif args.no_proxy:
        
        service_url = agent_url or get_cloud_run_service_url(args.project, args.region, agent_name)
        console.print(f"No proxy, connecting directly to {service_url}")

        return service_url
    
    else:
        # via gcloud proxy - requires gcloud auth access
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
        config = ConfigManager(args.vac_name)
        service_url = resolve_service_url(args)
        agent_name   = config.vacConfig("agent")

        streamer = can_agent_stream(agent_name)
        log.debug(f"streamer: {streamer}")
        if not streamer:
            console.print(f"Non streaming agent: {args.vac_name}")

        if args.headless:
            headless_mode(service_url, args.vac_name, args.user_input, args.chat_history, stream=streamer)
        else:
            display_name = config.vacConfig("display_name")
            description  = config.vacConfig("description")
            endpoints_config = config.agentConfig(agent_name)

            post_endpoints = endpoints_config['post']

            display_endpoints = ' '.join(f"{key}: {value}" for key, value in post_endpoints.items())
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
        # Try to load existing data from the file, or initialize an empty dict
    file_path = "config/cloud_run_urls.json"
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            services_dict = json.load(file)
    else:
        services_dict = {}

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

        # Update the services dictionary
        services_dict[service_name] = service_url

        # Write the updated dictionary back to the file
        with open(file_path, 'w') as file:
            json.dump(services_dict, file, indent=4)
            
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

    # If no subcommand is provided, print the help message
    vac_parser.set_defaults(func=lambda args: vac_parser.print_help() if args.action is None else vac_command(args))
