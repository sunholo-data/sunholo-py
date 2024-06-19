from ..agents.swagger import generate_swagger
from ..utils.config import load_all_configs, load_config
from .sun_rich import console

def cli_swagger(args):
    if not args.config_path:
        configs = load_all_configs()
        vac_config = configs.get('vacConfig')
        console.rule("Creating Swagger file from _CONFIG_FOLDER")
    else:
        vac_config = load_config(args.config_path)
        console.rule("Creating Swagger file from {args.config_path}")
    
    swag = generate_swagger(vac_config)

    console.print(swag)

    return swag

def setup_swagger_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'swagger' command.

    By default will use the 'vacConfig' configuration within the folder specified by '_CONFIG_FOLDER'

    Example command:
    ```bash
    sunholo swagger --config .
    ```
    """
    deploy_parser = subparsers.add_parser('swagger', help='Create a swagger specification based off a "vacConfig" configuration')
    deploy_parser.add_argument('--config_path', help='Path to the directory containing the config folder `config/`.  Set _CONFIG_FOLDER env var to change config location.')
    deploy_parser.set_defaults(func=cli_swagger)