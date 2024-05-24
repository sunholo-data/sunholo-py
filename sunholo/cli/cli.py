import argparse
try:
    from google.cloud import build_v1
except ImportError:
    build_v1 = None

from ..logging import log

def trigger_build(args):
    """
    Triggers a Google Cloud Build using an existing build trigger configured in GCP.

    Args:
        args: argparse.Namespace containing the command line arguments specified for the 'deploy' command.

    Example:
        trigger_build(args) where args contains project_id, trigger_id, repo_name, and branch_name.
    """
    if not build_v1:
        log.warning("Can't deploy - google-cloud-build not installed, enable via `pip install sunholo[gcp]")

        return None

    client = build_v1.services.cloud_build.CloudBuildClient()
    # Assuming the build source uses the path to the cloudbuild.yaml if specified.
    source = build_v1.RepoSource(
        project_id=args.project_id, 
        repo_name=args.repo_name, 
        branch_name=args.branch_name,
        substitutions=args.substitutions,
        dir=args.config_path  # Path to directory containing cloudbuild.yaml
    )
    request = build_v1.RunBuildTriggerRequest(
        project_id=args.project_id, 
        trigger_id=args.trigger_id, 
        source=source
    )
    operation = client.run_build_trigger(request)
    print(f"Triggered build with id: {operation.metadata.build.id}")

def setup_deploy_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'deploy' command.

    Example command:
    ```bash
    sunholo deploy --project_id "my-gcp-project" --trigger_id "my-trigger-id" --repo_name "my-repo"
    ```
    """
    deploy_parser = subparsers.add_parser('deploy', help='Triggers a deployment using an existing Google Cloud Build trigger.')
    deploy_parser.add_argument('--project_id', required=True, help='Google Cloud Project ID required for deployment.')
    deploy_parser.add_argument('--trigger_id', required=True, help='Google Cloud Build Trigger ID required for deployment.')
    deploy_parser.add_argument('--repo_name', required=True, help='Name of the linked repository in Google Cloud Source Repositories required for deployment.')
    deploy_parser.add_argument('--branch_name', default='main', help='Branch name to trigger the build from, defaults to "main".')
    deploy_parser.add_argument('--config_path', default='.', help='Path to the directory containing the cloudbuild.yaml file, defaults to current directory.')
    deploy_parser.set_defaults(func=trigger_build)

def main(args=None):
    """
    Entry point for the sunholo console script. This function parses command line arguments
    and invokes the appropriate functionality based on the user input.

    Example commands:
    ```bash
    sunholo deploy --project_id "my-gcp-project" --trigger_id "my-trigger-id" --repo_name "my-repo" --branch_name "dev" --config_path "app/vac/my_vac/"
    ```
    """
    parser = argparse.ArgumentParser(description="sunholo CLI tool for deploying applications using Google Cloud Build.")
    subparsers = parser.add_subparsers(title='commands', description='Valid commands', help='`sunholo deploy --help`', dest='command', required=True)

    # Setup deploy command
    setup_deploy_subparser(subparsers)

    args = parser.parse_args(args)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
