import sys
from ..utils.config import load_all_configs
from ..utils.config_schema import SCHEMAS, VAC_SUBCONFIG_SCHEMA

from jsonschema import validate, ValidationError
from pprint import pprint

def validate_config(config, schema):
    try:
        validate(instance=config, schema=schema)
        print("OK: Validated schema")
        return True
    except ValidationError as err:
        error_path = " -> ".join(map(str, err.path))
        print(f"ERROR: Validation error at '{error_path}': {err.message}")
        return False

def list_configs(args):
    """
    Lists configuration files, filtered by kind or VAC name if specified, and optionally validates them.

    Args:
        args: Command-line arguments including 'kind', 'vac', and 'validate' for filtering and validation.

    Examples:
        # List all configurations
        list_configs(args)

        # List configurations filtered by kind
        args.kind = 'vacConfig'
        list_configs(args)

        # List configurations filtered by VAC name
        args.vac = 'edmonbrain'
        list_configs(args)

        # List configurations filtered by both kind and VAC name
        args.kind = 'vacConfig'
        args.vac = 'edmonbrain'
        list_configs(args)

        # Validate configurations
        args.validate = True
        list_configs(args)
    """
    print("Listing configuration files")
    configs = load_all_configs()
    filtered_configs = {}

    if args.kind and args.vac:
        if args.kind in configs:
            kind_config = configs[args.kind]
            vac_config = kind_config.get('vac', {}).get(args.vac)
            if vac_config:
                filtered_configs[args.kind] = {args.vac: vac_config}
            else:
                print(f"No configurations found for kind: {args.kind} with VAC: {args.vac}")
        else:
            print(f"No configurations found for kind: {args.kind}")
    elif args.kind:
        if args.kind in configs:
            filtered_configs[args.kind] = configs[args.kind]
        else:
            print(f"No configurations found for kind: {args.kind}")
    elif args.vac:
        for kind, config in configs.items():
            vac_config = config.get('vac', {}).get(args.vac)
            if vac_config:
                if kind not in filtered_configs:
                    filtered_configs[kind] = {}
                filtered_configs[kind][args.vac] = vac_config
        if not filtered_configs:
            print(f"No configurations found with VAC: {args.vac}")
    else:
        filtered_configs = configs

    for kind, config in filtered_configs.items():
        print(f"## Config kind: {kind}")
        pprint(config)

    if args.validate:
        validation_failed = False
        for kind, config in filtered_configs.items():
            print(f"Validating configuration for kind: {kind}")
            if args.kind == "vacConfig" and args.vac:
                print(f"Validating vacConfig for {args.vac}")
                if not validate_config(config[args.vac], VAC_SUBCONFIG_SCHEMA):
                    print(f"Validation failed for sub-kind: {args.vac}")
                    validation_failed = True
            elif kind in SCHEMAS:
                if not validate_config(config, SCHEMAS[kind]):
                    print(f"FAIL: Validation failed for kind: {kind}")
                    validation_failed = True
            else:
                print(f"No schema available to validate configuration for kind: {kind}")

        if validation_failed:
            print("Validation failed for one or more configurations")

            sys.exit(1)


def setup_list_configs_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'list-configs' command.

    Args:
        subparsers: The subparsers object from argparse.ArgumentParser().

    Examples:
        # Set up the subparser for the 'list-configs' command
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        setup_list_configs_subparser(subparsers)
    """
    list_configs_parser = subparsers.add_parser('list-configs', help='Lists all configuration files and their details')
    list_configs_parser.add_argument('--kind', help='Filter configurations by kind e.g. `--kind=vacConfig`')
    list_configs_parser.add_argument('--vac', help='Filter configurations by VAC name e.g. `--vac=edmonbrain`')
    list_configs_parser.add_argument('--validate', action='store_true', help='Validate the configuration files.')
    list_configs_parser.set_defaults(func=list_configs)
