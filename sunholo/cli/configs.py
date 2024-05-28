from ..utils.config import load_all_configs
from ..logging import log

from pprint import pprint

def list_configs(args):
    """
    Lists configuration files, filtered by kind if specified.
    """
    log.info("Listing configuration files")
    configs = load_all_configs()

    if args.kind:
        if args.kind in configs:
            print(f"## Config kind: {args.kind}")
            pprint(configs[args.kind])
        else:
            print(f"No configurations found for kind: {args.kind}")
    else:
        for kind, config in configs.items():
            pprint(f"## Config kind: {kind}") 
            pprint(config)

def setup_list_configs_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'list-configs' command.
    """
    list_configs_parser = subparsers.add_parser('list-configs', help='Lists all configuration files and their details.')
    list_configs_parser.add_argument('--kind', help='Filter configurations by kind.')
    list_configs_parser.set_defaults(func=list_configs)
