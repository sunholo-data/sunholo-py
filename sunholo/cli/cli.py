import argparse

from .configs import setup_list_configs_subparser
from .deploy import setup_deploy_subparser
from .cli_init import setup_init_subparser
from .merge_texts import setup_merge_text_subparser
from .run_proxy import setup_proxy_subparser
from .chat_vac import setup_vac_subparser


def main(args=None):
    """
    Entry point for the sunholo console script. This function parses command line arguments
    and invokes the appropriate functionality based on the user input.

    Example commands:
    ```bash
    sunholo deploy --config_path . --gcs_bucket your-gcs-bucket --lancedb_bucket your-lancedb-bucket
    ```
    """
    parser = argparse.ArgumentParser(description="sunholo CLI tool for deploying GenAI VACs")
    subparsers = parser.add_subparsers(title='commands', 
                                       description='Valid commands', 
                                       help='Commands', 
                                       dest='command', 
                                       required=True)

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

    args = parser.parse_args(args)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
