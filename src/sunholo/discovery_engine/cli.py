import json

try:
    from ..cli.sun_rich import console
except ImportError:
    console = None

from ..custom_logging import log

# Make sure to adjust the relative import path if needed
from .discovery_engine_client import DiscoveryEngineClient  

def discovery_engine_command(args):
    """
    Handles the `discovery-engine` command and its subcommands.
    """
    if args.subcommand == 'create-datastore':
        create_datastore_command(args)
    elif args.subcommand == 'import-documents':
        import_documents_command(args)
    elif args.subcommand == 'import-documents-with-metadata':
        import_documents_with_metadata_command(args)
    elif args.subcommand == 'import-document-with-metadata':
        import_document_with_metadata_command(args)
    elif args.subcommand == 'search':
        search_command(args)
    elif args.subcommand == 'search-by-id-and-or-date':
        search_by_id_and_or_date_command(args)
    else:
        console.print(f"[bold red]Unknown Discovery Engine subcommand: {args.subcommand}[/bold red]")

def create_datastore_command(args):
    """
    Handles the `discovery-engine create-datastore` subcommand.
    """
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id,
            location=args.location
        )
        operation_name = client.create_data_store(
            type=args.type,
            chunk_size=args.chunk_size,
            collection=args.collection
        )
        console.print(f"[bold green]Datastore creation initiated. Operation name: {operation_name}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error creating datastore: {e}[/bold red]")

def import_documents_command(args):
    """
    Handles the `discovery-engine import-documents` subcommand.
    """
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id,
            location=args.location
        )
        operation_name = client.import_documents(
            gcs_uri=args.gcs_uri,
            data_schema=args.data_schema,
            branch=args.branch,
            bigquery_dataset=args.bigquery_dataset,
            bigquery_table=args.bigquery_table,
            bigquery_project_id=args.bigquery_project_id
        )
        console.print(f"[bold green]Document import initiated. Operation name: {operation_name}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error importing documents: {e}[/bold red]")

def import_documents_with_metadata_command(args):
    """
    Handles the `discovery-engine import-documents-with-metadata` subcommand.
    """
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id,
            location=args.location
        )
        operation_name = client.import_documents_with_metadata(
            gcs_uri=args.gcs_uri,
            data_schema=args.data_schema,
            branch=args.branch
        )
        console.print(f"[bold green]Document import with metadata initiated. Operation name: {operation_name}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error importing documents with metadata: {e}[/bold red]")

def import_document_with_metadata_command(args):
    """
    Handles the `discovery-engine import-document-with-metadata` subcommand.
    """
    try:
        # Load metadata from JSON file or string
        if args.metadata_file:
            with open(args.metadata_file, 'r') as f:
                metadata = json.load(f)
        elif args.metadata_string:
            metadata = json.loads(args.metadata_string)
        else:
            console.print("[bold red]Error: Must provide either --metadata-file or --metadata-string[/bold red]")
            return

        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id,
            location=args.location
        )
        operation_name = client.import_document_with_metadata(
            gcs_uri=args.gcs_uri,
            metadata=metadata,
            branch=args.branch
        )
        console.print(f"[bold green]Document import with metadata initiated. Operation name: {operation_name}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error importing document with metadata: {e}[/bold red]")

def search_command(args):
    """
    Handles the `discovery-engine search` subcommand.
    """
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id,
            location=args.location
        )
        results = client.get_chunks(
            query=args.query,
            num_previous_chunks=args.num_previous_chunks,
            num_next_chunks=args.num_next_chunks,
            page_size=args.page_size,
            parse_chunks_to_string=args.parse_chunks_to_string,
            serving_config=args.serving_config,
            data_store_ids=args.data_store_ids
        )

        if args.parse_chunks_to_string:
            console.print(results)  # Print the combined string
        else:
            # Process and print the results (assuming it's a SearchResponse object)
            for result in results.results:
                for chunk in result.document.chunks:
                    console.print(f"Chunk: {chunk.snippet}, document name: {chunk.document_name}")
    except Exception as e:
        console.print(f"[bold red]Error searching: {e}[/bold red]")

def search_by_id_and_or_date_command(args):
    """
    Handles the `discovery-engine search-by-id-and-or-date` subcommand.
    """
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id,
            location=args.location
        )
        results = client.search_by_objectId_and_or_date(
            query=args.query,
            objectId=args.object_id,
            date=args.date,
            num_previous_chunks=args.num_previous_chunks,
            num_next_chunks=args.num_next_chunks,
            page_size=args.page_size,
            parse_chunks_to_string=args.parse_chunks_to_string,
            serving_config=args.serving_config,
            data_store_ids=args.data_store_ids
        )

        if args.parse_chunks_to_string:
            console.print(results)  # Print the combined string
        else:
            # Process and print the results (assuming it's a SearchResponse object)
            for result in results.results:
                for chunk in result.document.chunks:
                    console.print(f"Chunk: {chunk.snippet}, document name: {chunk.document_name}")
    except Exception as e:
        console.print(f"[bold red]Error searching by ID and/or date: {e}[/bold red]")

def setup_discovery_engine_subparser(subparsers):
    """
    Sets up the `discovery-engine` subparser and its subcommands.
    """
    discovery_engine_parser = subparsers.add_parser('discovery-engine', help='Interact with Google Cloud Discovery Engine')
    discovery_engine_subparsers = discovery_engine_parser.add_subparsers(dest='subcommand', required=True)

    # Create Datastore subcommand
    create_datastore_parser = discovery_engine_subparsers.add_parser('create-datastore', help='Create a new Discovery Engine datastore')
    create_datastore_parser.add_argument('--data-store-id', required=True, help='The ID of the datastore')
    create_datastore_parser.add_argument('--type', choices=['chunk'], default='chunk', help='The type of datastore to create')
    create_datastore_parser.add_argument('--chunk-size', type=int, default=500, help='The size of the chunks for documents (if applicable)')
    create_datastore_parser.add_argument('--collection', default='default_collection', help='The collection to create the datastore in')
    create_datastore_parser.set_defaults(func=discovery_engine_command)

    # Import Documents subcommand
    import_documents_parser = discovery_engine_subparsers.add_parser('import-documents', help='Import documents into a Discovery Engine datastore')
    import_documents_parser.add_argument('--gcs-uri', required=True, help='The GCS URI of the documents to import')
    import_documents_parser.add_argument('--data-schema', default='content', help='The schema of the data to import')
    import_documents_parser.add_argument('--branch', default='default_branch', help='The branch to import the documents into')
    import_documents_parser.add_argument('--bigquery-dataset', help='The BigQuery dataset ID (if applicable)')
    import_documents_parser.add_argument('--bigquery-table', help='The BigQuery table ID (if applicable)')
    import_documents_parser.add_argument('--bigquery-project-id', help='The project ID of the BigQuery dataset (if applicable)')
    import_documents_parser.set_defaults(func=discovery_engine_command)

    # Import Documents with Metadata subcommand
    import_documents_with_metadata_parser = discovery_engine_subparsers.add_parser('import-documents-with-metadata', help='Import documents with metadata into a Discovery Engine datastore')
    import_documents_with_metadata_parser.add_argument('--gcs-uri', required=True, help='The GCS URI of the documents to import (JSONL format with metadata)')
    import_documents_with_metadata_parser.add_argument('--data-schema', default='content', help='The schema of the data to import')
    import_documents_with_metadata_parser.add_argument('--branch', default='default_branch', help='The branch to import the documents into')
    import_documents_with_metadata_parser.set_defaults(func=discovery_engine_command)

    # Import Document with Metadata subcommand
    import_document_with_metadata_parser = discovery_engine_subparsers.add_parser('import-document-with-metadata', help='Import a single document with metadata into a Discovery Engine datastore')
    import_document_with_metadata_parser.add_argument('--gcs-uri', required=True, help='The GCS URI of the document to import')
    import_document_with_metadata_parser.add_argument('--metadata-file', help='The path to a JSON file containing the metadata')
    import_document_with_metadata_parser.add_argument('--metadata-string', help='A JSON string containing the metadata')
    import_document_with_metadata_parser.add_argument('--branch', default='default_branch', help='The branch to import the document into')
    import_document_with_metadata_parser.set_defaults(func=discovery_engine_command)

    # Search subcommand
    search_parser = discovery_engine_subparsers.add_parser('search', help='Search a Discovery Engine datastore')
    search_parser.add_argument('--query', required=True, help='The search query')
    search_parser.add_argument('--data-store-id', required=True, help='Data store ID to search')
    search_parser.add_argument('--page-size', type=int, default=10, help='The maximum number of results to return per page')
    search_parser.add_argument('--parse-chunks-to-string', action='store_true', help='Combine chunks into a single string')
    search_parser.add_argument('--serving-config', default='default_serving_config', help='The serving configuration to use')

    search_parser.set_defaults(func=discovery_engine_command)

    # Search by ID and/or Date subcommand
    search_by_id_and_or_date_parser = discovery_engine_subparsers.add_parser('search-by-id-and-or-date', help='Search a Discovery Engine datastore by object ID and/or date')
    search_by_id_and_or_date_parser.add_argument('--query', required=True, help='The search query')
    search_by_id_and_or_date_parser.add_argument('--object-id', help='The exact object ID to filter by')
    search_by_id_and_or_date_parser.add_argument('--date', help='The date to filter by (YYYY-MM-DD)')
    search_by_id_and_or_date_parser.add_argument('--num-previous-chunks', type=int, default=3, help='Number of previous chunks to return for context')
    search_by_id_and_or_date_parser.add_argument('--num-next-chunks', type=int, default=3, help='Number of next chunks to return for context')
    search_by_id_and_or_date_parser.add_argument('--page-size', type=int, default=10, help='The maximum number of results to return per page')
    search_by_id_and_or_date_parser.add_argument('--parse-chunks-to-string', action='store_true', help='Combine chunks into a single string')
    search_by_id_and_or_date_parser.add_argument('--serving-config', default='default_serving_config', help='The serving configuration to use')
    search_by_id_and_or_date_parser.add_argument('--data-store-ids', nargs='+', help='List of data store IDs to search (optional)')
    search_by_id_and_or_date_parser.set_defaults(func=discovery_engine_command)