import subprocess
import os
import signal
import json

from .sun_rich import console
from rich.table import Table
from rich import print

PROXY_TRACKER_FILE = '.vac_proxy_tracker.json'
DEFAULT_PORT = 8080

def create_hyperlink(url, text):
    """
    Creates a hyperlink for the console.

    Args:
        url (str): The URL for the hyperlink.
        text (str): The text to display for the hyperlink.

    Returns:
        str: The formatted hyperlink.
    """
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def get_next_available_port(proxies, default_port):
    """
    Get the next available port starting from the default port.

    Args:
        proxies (dict): Current proxies with their assigned ports.
        default_port (int): Default starting port.

    Returns:
        int: The next available port.
    """
    used_ports = {info["port"] for info in proxies.values()}
    port = default_port
    while port in used_ports:
        port += 1
    return port

def check_gcloud():
    """
    Checks if gcloud is installed and authenticated.

    Returns:
        bool: True if gcloud is installed and authenticated, False otherwise.
    """
    try:
        # Check if gcloud is installed
        result = subprocess.run(["gcloud", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if result.returncode != 0:
            print("[bold red]ERROR: gcloud is not installed or not found in PATH.[/bold red]")
            return False

        # Check if gcloud is authenticated
        result = subprocess.run(["gcloud", "auth", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if result.returncode != 0 or "ACTIVE" not in result.stdout.decode():
            print("ERROR: gcloud is not authenticated. Please run 'gcloud auth login'.")
            return False

        print("gcloud is installed and authenticated.")
        return True
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        return False

def is_process_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        print("WARNING: VAC Proxy lost connection")
        return False

def load_proxies():
    if os.path.exists(PROXY_TRACKER_FILE):
        with open(PROXY_TRACKER_FILE, 'r') as file:
            return json.load(file)
    return {}

def clean_proxy_list():
    proxies = load_proxies()
    updated_proxies = {k: v for k, v in proxies.items() if is_process_running(v["pid"])}
    if len(proxies) != len(updated_proxies):
        save_proxies(updated_proxies)
        
    return updated_proxies

def save_proxies(proxies):
    with open(PROXY_TRACKER_FILE, 'w') as file:
        json.dump(proxies, file, indent=4)




def start_proxy(service_name, region, project, port=None):
    """
    Starts the gcloud proxy to the Cloud Run service and stores the PID.

    Args:
        service_name (str): Name of the Cloud Run service.
        region (str): Region of the Cloud Run service.
        project (str): GCP project of the Cloud Run service.
        port (int, optional): Port to run the proxy on. If not provided, auto-assigns the next available port.
    """
    proxies = clean_proxy_list()

    if service_name in proxies:
        console.print(f"Proxy for service [bold orange]'{service_name}'[/bold orange] is already running on port {proxies[service_name]['port']}.")
        return

    if not port:
        port = get_next_available_port(proxies, DEFAULT_PORT)

    command = [
        "gcloud", "run", "services", "proxy", service_name,
        "--region", region,
        "--project", project,
        "--port", str(port)
    ]
    with open(os.devnull, 'w') as devnull:
        process = subprocess.Popen(command, stdout=devnull, stderr=devnull, preexec_fn=os.setpgrp)
    
    proxies[service_name] = {
        "pid": process.pid,
        "port": port
    }
    save_proxies(proxies)
    
    console.print(f"Proxy for [bold orange]'{service_name}'[/bold orange] setup complete on port {port}")
    list_proxies()

    return f"http://127.0.0.1:{port}"


def stop_proxy(service_name):
    """
    Stops the gcloud proxy to the Cloud Run service using the stored PID.

    Args:
        service_name (str): Name of the Cloud Run service.
    """
    proxies = clean_proxy_list()

    if service_name not in proxies:
        print(f"No proxy found for service: {service_name}")
        return

    pid = proxies[service_name]["pid"]
    try:
        os.kill(pid, signal.SIGTERM)
        del proxies[service_name]
        save_proxies(proxies)
        console.print(f"Proxy for [bold orange]'{service_name}'[bold orange] stopped.")
    except ProcessLookupError:
        console.print(f"No process found with PID: {pid}")
    except Exception as e:
        console.print(f"[bold red]Error stopping proxy for {service_name}: {e}[/bold red]")
    
    list_proxies()

def stop_all_proxies():
    """
    Stops all running gcloud proxies.
    """
    proxies = clean_proxy_list()

    for service_name, info in proxies.items():
        pid = info["pid"]
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Proxy for [bold orange]'{service_name}'[/bold orange] stopped.")
        except ProcessLookupError:
            print(f"No process found with PID: {pid}")
        except Exception as e:
            print(f"Error stopping proxy for [bold orange]'{service_name}'[/bold orange]: {e}")
    
    save_proxies({})

    list_proxies()

def list_proxies():
    """
    Lists all running proxies.
    """
    with console.status("[bold orange]Listing Proxies[/bold orange]", spinner="star"):
        proxies = clean_proxy_list()

    if not proxies:
        print("No proxies currently running.")
    else:
        table = Table(title="VAC Proxies")
        table.add_column("VAC")
        table.add_column("Port")
        table.add_column("PID")
        table.add_column("URL")
        
        for service_name, info in proxies.items():
            url = f"http://127.0.0.1:{info['port']}"
            table.add_row(service_name, str(info['port']), str(info['pid']), url)
        
        console.print(table)

def setup_proxy_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'proxy' command.

    Args:
        subparsers: The subparsers object from argparse.ArgumentParser().
    """
    
    proxy_parser = subparsers.add_parser('proxy', help='Set up or stop a proxy to the VAC Cloud Run services')
    proxy_subparsers = proxy_parser.add_subparsers(dest='proxy_command', required=True)

    start_parser = proxy_subparsers.add_parser('start', help='Start the proxy to the VAC Cloud Run service')
    start_parser.add_argument('service_name', help='Name of the Cloud Run service.')
    start_parser.add_argument('--port', type=int, help='Port to run the proxy on. Auto-assigns if not provided.')
    start_parser.set_defaults(func=lambda args: start_proxy(args.service_name, args.region, args.project, args.port))

    stop_parser = proxy_subparsers.add_parser('stop', help='Stop the proxy to the Cloud Run service.')
    stop_parser.add_argument('service_name', help='Name of the Cloud Run service.')
    stop_parser.set_defaults(func=lambda args: stop_proxy(args.service_name))

    list_parser = proxy_subparsers.add_parser('list', help='List all running proxies.')
    list_parser.set_defaults(func=lambda args: list_proxies())

    stop_all_parser = proxy_subparsers.add_parser('stop-all', help='Stop all running proxies.')
    stop_all_parser.set_defaults(func=lambda args: stop_all_proxies())



