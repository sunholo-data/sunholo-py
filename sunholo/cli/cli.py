import argparse
import logging

from .configs import setup_list_configs_subparser
from .deploy import setup_deploy_subparser
from .cli_init import setup_init_subparser
from .merge_texts import setup_merge_text_subparser
from .run_proxy import setup_proxy_subparser
from .chat_vac import setup_vac_subparser
from .embedder import setup_embedder_subparser
from .swagger import setup_swagger_subparser
from .vertex import setup_vertex_subparser
from ..llamaindex import setup_llamaindex_subparser
from ..excel import setup_excel_subparser
from ..terraform import setup_tfvarseditor_subparser

from ..utils import ConfigManager
from ..utils.version import sunholo_version

from ..custom_logging import log

from .sun_rich import console
import sys
from rich.panel import Panel

def load_default_gcp_config():
    try:
        gcp_config = ConfigManager("global").vacConfig("gcp_config")
    except FileNotFoundError as e:
        console.print(f"{e} - move config/ folder to working directory or set the VAC_CONFIG_FOLDER environment variable to its location")
        sys.exit(1)

    if gcp_config:
        return gcp_config.get('project_id', ''), gcp_config.get('location', 'europe-west1')
    else:
        return '', 'europe-west1'

class CustomHelpAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=0, **kwargs):
        super().__init__(option_strings, dest, nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        console.print(
            Panel("Welcome to Sunholo Command Line Interface, your assistant to deploy GenAI Virtual Agent Computers (VACs) to Multivac or your own Cloud.", 
                    title="Sunholo GenAIOps Assistant CLI",
                    subtitle="Documentation at https://dev.sunholo.com/")
        )
        console.rule()
        parser.print_help()
        parser.exit()

def main(args=None):
    """
    Entry point for the sunholo console script. This function parses command line arguments
    and invokes the appropriate functionality based on the user input.

    Get started:
    ```bash
    sunholo --help
    ```
    """
    default_project, default_region = load_default_gcp_config()

    parser = argparse.ArgumentParser(description="sunholo CLI tool for deploying GenAI VACs", add_help=False)
    parser.add_argument('-h', '--help', action=CustomHelpAction, help='Show this help message and exit')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--project', default=default_project, help='GCP project to list Cloud Run services from.')
    parser.add_argument('--region', default=default_region, help='Region to list Cloud Run services from.')
    parser.add_argument('-v', '--version', action='store_true', help='Show the version and exit')

    subparsers = parser.add_subparsers(title='commands', 
                                       description='Valid commands', 
                                       help='Commands', 
                                       dest='command', 
                                       required=False)

    # deploy command
    setup_deploy_subparser(subparsers)
    # Setup list-configs command
    setup_list_configs_subparser(subparsers)
    # init command
    setup_init_subparser(subparsers)
    # merge-text command
    setup_merge_text_subparser(subparsers)
    # proxy command
    setup_proxy_subparser(subparsers)
    # vac command
    setup_vac_subparser(subparsers)
    # embed command
    setup_embedder_subparser(subparsers)
    # swagger generation
    setup_swagger_subparser(subparsers)
    # vertex
    setup_vertex_subparser(subparsers)
    # llamaindex
    setup_llamaindex_subparser(subparsers)
    # excel
    setup_excel_subparser(subparsers)
    # terraform
    setup_tfvarseditor_subparser(subparsers)

    #TODO: add database setup commands: alloydb and supabase

    args = parser.parse_args(args)

    # Handle global flags
    if args.version:
        console.print(sunholo_version())
        return

    if args.debug:
        log.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARNING)
        logging.getLogger().setLevel(logging.WARNING)

    # Handle subcommand
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

