from ..vertex import VertexAIExtensions  

from .sun_rich import console

def deploy_extension(args):
    vex = VertexAIExtensions(args.project)
    console.rule(f"Creating Vertex extension '{args.display_name}' within '{args.project}'")

    vex.create_extension(
        args.display_name,
        description=args.description,
        tool_example_file=args.tool_example_file,
        open_api_file=args.open_api_file,
        service_account=args.service_account,
        bucket_name=args.bucket_name
    )
    extensions = vex.list_extensions()
    console.print(extensions)

def list_extensions(args):
    vex = VertexAIExtensions(args.project)
    extensions = vex.list_extensions()
    console.print(extensions)

def setup_vertex_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'vertex' command.

    Args:
        subparsers: The subparsers object to add the 'vertex' subcommand to.
    """
    vertex_parser = subparsers.add_parser('vertex', help='Work with Google Vertex AI')
    vertex_subparsers = vertex_parser.add_subparsers(dest='subcommand', help='Vertex AI subcommands')

    create_parser = vertex_subparsers.add_parser('create-extension', help='Create a Vertex AI extension')
    create_parser.add_argument('--display_name', required=True, help='Display name of the extension')
    create_parser.add_argument('--description', required=True, help='Description of the extension')
    create_parser.add_argument('--tool_example_file', required=True, help='Tool example file path')
    create_parser.add_argument('--open_api_file', required=True, help='OpenAPI file path')
    create_parser.add_argument('--service_account', required=True, help='Service account email')
    create_parser.add_argument('--bucket_name', help='Bucket name to upload files to.  Uses EXTENSION_BUCKET env var if not specified')
    create_parser.set_defaults(func=deploy_extension)

    list_parser = vertex_subparsers.add_parser('list-extensions', help='List all Vertex AI extensions')
    list_parser.set_defaults(func=list_extensions)