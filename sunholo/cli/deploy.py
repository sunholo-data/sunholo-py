import os
from subprocess import Popen
from ..utils.config import load_all_configs

def deploy_vac(args):
    """
    Deploys the VAC by running a Flask app locally.
    """
    print(f"Deploying VAC: {args.vac_name} locally")

    # Load the vacConfig
    configs_by_kind = load_all_configs()
    vac_config = configs_by_kind.get('vacConfig', {}).get('vac', {}).get(args.vac_name)

    if not vac_config:
        raise ValueError(f"No configuration found for VAC: {args.vac_name}")

    # Assuming the Flask app is in 'app.py' within the config path
    app_path = os.path.join(args.config_path, 'app.py')
    if not os.path.exists(app_path):
        raise ValueError(f"app.py not found in {args.config_path}")

    print(f"Running Flask app from {app_path}")

    # Run the Flask app
    command = ["python", app_path]
    print(f"Running Flask app with command: {' '.join(command)}")
    process = Popen(command)
    process.communicate()

def setup_deploy_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'deploy' command.

    Example command:
    ```bash
    sunholo deploy "vac_name" --config_path .
    ```
    """
    deploy_parser = subparsers.add_parser('deploy', help='Triggers a deployment of a VAC.')
    deploy_parser.add_argument('vac_name', help='The name of the VAC to deploy.')
    deploy_parser.add_argument('--config_path', default='.', help='Path to the directory containing the config folder `config/` and Flask app `app.py`, defaults to current directory.  Set _CONFIG_FOLDER env var to change config location.')
    deploy_parser.set_defaults(func=deploy_vac)
