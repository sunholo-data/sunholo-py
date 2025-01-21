from ..agents.swagger import generate_swagger
from ..utils.config import load_all_configs
from ruamel.yaml import YAML
import sys

def cli_swagger(args):

    configs = load_all_configs()

    vac_config = args.vac_config_path or configs.get('vacConfig')
    agent_config = args.agent_config_path or configs.get('agentConfig')
    if not agent_config:
        raise ValueError('Need an agentConfig path')

    if not vac_config:
        raise ValueError('Need a vacConfig path')
    
    swag = generate_swagger(vac_config, agent_config)

    yaml = YAML()
    yaml.width = 4096 # to avoid breaking urls
    yaml.indent(mapping=2, sequence=4, offset=2)  # Set indentation levels

    yaml.dump(yaml.load(swag), sys.stdout) 

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
    deploy_parser.add_argument('--vac_config_path', help='Path to the vacConfig file.  Set _CONFIG_FOLDER env var and place file in there to change default config location.')
    deploy_parser.add_argument('--agent_config_path', help='Path to agentConfig file. Set _CONFIG_FOLDER env var and place file in there to change default config location.')
    deploy_parser.set_defaults(func=cli_swagger)
