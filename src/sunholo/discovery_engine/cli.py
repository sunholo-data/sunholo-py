import json
import argparse
import traceback # For detailed error logging

# --- Standard library imports first ---
# --- Third-party imports ---
try:
    # Assuming sun_rich is in your project structure relative to this file
    from ..cli.sun_rich import console
    from google.protobuf.json_format import MessageToDict
    import proto
except ImportError:
    # Fallback if rich is not available or path is wrong
    class ConsoleFallback:
        def print(self, *args, **kwargs):
            print(*args)
    console = ConsoleFallback()
    print("Warning: rich console not found, using basic print.")

# --- Local application imports ---
# Assuming custom_logging is available
# from ..custom_logging import log # Not explicitly used in CLI functions here

# Make sure to adjust the relative import path if needed for your project structure
from .discovery_engine_client import DiscoveryEngineClient, _DISCOVERYENGINE_AVAILABLE

# Import necessary types only if library is available, for mapping CLI args
if _DISCOVERYENGINE_AVAILABLE:
    from .discovery_engine_client import discoveryengine # Get the imported module
else:
    discoveryengine = None # Set to None if import failed


def convert_composite_to_native(value):
    """
    Recursively converts a proto MapComposite or RepeatedComposite object to native Python types.

    Args:
        value: The proto object, which could be a MapComposite, RepeatedComposite, or a primitive.

    Returns:
        The equivalent Python dictionary, list, or primitive type.
    """
    if isinstance(value, proto.marshal.collections.maps.MapComposite):
        # Convert MapComposite to a dictionary, recursively processing its values
        return {key: convert_composite_to_native(val) for key, val in value.items()}
    elif isinstance(value, proto.marshal.collections.repeated.RepeatedComposite):
        # Convert RepeatedComposite to a list, recursively processing its elements
        return [convert_composite_to_native(item) for item in value]
    else:
        # If it's a primitive value, return it as is
        return value

# --- Command Handler Functions ---

def discovery_engine_command(args):
    """
    Handles the `discovery-engine` command and its subcommands.
    """
    # Dispatch based on subcommand
    if args.subcommand == 'create-datastore':
        create_datastore_command(args)
    elif args.subcommand == 'import-documents':
        import_documents_command(args)
    elif args.subcommand == 'import-documents-with-metadata':
        import_documents_with_metadata_command(args)
    elif args.subcommand == 'import-document-with-metadata':
        import_document_with_metadata_command(args)
    elif args.subcommand == 'search': # Existing chunk search
        search_command(args)
    elif args.subcommand == 'search-by-id-and-or-date': # Existing chunk search
        search_by_id_and_or_date_command(args)
    elif args.subcommand == 'search-engine': # NEW engine search
        search_engine_command(args)
    # Add elif for create-engine if needed
    # elif args.subcommand == 'create-engine':
    #    create_engine_command(args)
    else:
        console.print(f"[bold red]Unknown Discovery Engine subcommand: {args.subcommand}[/bold red]")

def create_datastore_command(args):
    """Handles the `discovery-engine create-datastore` subcommand."""
    console.print(f"[cyan]Initiating datastore creation for ID: {args.data_store_id}...[/cyan]")
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id, # ID for the one being created
            location=args.location
        )
        # Assuming create_data_store exists and takes these args
        operation_name = client.create_data_store(
            type=args.type,
            chunk_size=args.chunk_size,
            collection=args.collection
        )
        console.print(f"[bold green]Datastore creation initiated. Operation name: {operation_name}[/bold green]")
        console.print("[yellow]Note: Creation is asynchronous. Check operation status in Google Cloud Console.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error creating datastore: {e}[/bold red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")

def import_documents_command(args):
    """Handles the `discovery-engine import-documents` subcommand."""
    console.print(f"[cyan]Initiating document import into datastore: {args.data_store_id}...[/cyan]")
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id, # Target datastore
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
        if operation_name:
            console.print(f"[bold green]Document import initiated. Operation name: {operation_name}[/bold green]")
            console.print("[yellow]Note: Import is asynchronous. Check operation status in Google Cloud Console.[/yellow]")
        else:
             console.print("[bold yellow]Document import command executed, but no operation name returned (may indicate skipped due to existing data or other non-fatal issue). Check logs.[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error importing documents: {e}[/bold red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")

def import_documents_with_metadata_command(args):
    """Handles the `discovery-engine import-documents-with-metadata` subcommand."""
    console.print(f"[cyan]Initiating document import with metadata from {args.gcs_uri} into datastore: {args.data_store_id}...[/cyan]")
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id,
            location=args.location
        )
        # Ensure the method exists in your client class
        operation_name = client.import_documents_with_metadata(
            gcs_uri=args.gcs_uri,
            # data_schema=args.data_schema, # This method might not need data_schema explicitly
            branch=args.branch
        )
        if operation_name:
            console.print(f"[bold green]Document import with metadata initiated. Operation name: {operation_name}[/bold green]")
            console.print("[yellow]Note: Import is asynchronous.[/yellow]")
        else:
             console.print("[bold yellow]Document import command executed, but no operation name returned.[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error importing documents with metadata: {e}[/bold red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")

def import_document_with_metadata_command(args):
    """Handles the `discovery-engine import-document-with-metadata` subcommand."""
    console.print(f"[cyan]Initiating single document import with metadata for {args.gcs_uri} into datastore: {args.data_store_id}...[/cyan]")
    metadata = None
    try:
        if args.metadata_file:
            console.print(f"Loading metadata from file: {args.metadata_file}")
            with open(args.metadata_file, 'r') as f:
                metadata = json.load(f)
        elif args.metadata_string:
            console.print("Loading metadata from string.")
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
        if operation_name:
            console.print(f"[bold green]Single document import initiated. Operation name: {operation_name}[/bold green]")
            console.print("[yellow]Note: Import is asynchronous.[/yellow]")
        else:
             console.print("[bold yellow]Single document import command executed, but no operation name returned.[/bold yellow]")

    except FileNotFoundError:
         console.print(f"[bold red]Error: Metadata file not found at {args.metadata_file}[/bold red]")
    except json.JSONDecodeError as e:
         console.print(f"[bold red]Error decoding metadata JSON: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error importing document with metadata: {e}[/bold red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")

def search_command(args):
    """Handles the `discovery-engine search` subcommand (Data Store Chunks)."""
    console.print(f"[cyan]Searching data store '{args.data_store_id}' for query: '{args.query}' (mode: {args.content_search_spec_type})[/cyan]")
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id, # Target datastore
            location=args.location
        )

        if args.content_search_spec_type == "chunks":
            # This calls get_chunks which returns string or pager
            results_data = client.get_chunks(
                query=args.query,
                # num_previous_chunks=args.num_previous_chunks, # Ensure these args are added to parser if needed
                # num_next_chunks=args.num_next_chunks, # Ensure these args are added to parser if needed
                page_size=args.page_size,
                parse_chunks_to_string=args.parse_chunks_to_string,
                serving_config=args.serving_config,
                filter_str=args.filter,
            )
        elif args.content_search_spec_type == "documents":
            results_data = client.get_documents(
                query=args.query,
                page_size=args.page_size,
                parse_documents_to_string=args.parse_chunks_to_string,
                serving_config=args.serving_config,
                filter_str=args.filter,
            )  
        else:
            raise ValueError("Invalid content_search_spec_type. Must be 'chunks' or 'documents'.")          

        if args.parse_chunks_to_string:
            console.print("\n[bold magenta]--- Combined Chunk String ---[/bold magenta]")
            console.print(results_data if results_data else "[yellow]No results found or error occurred.[/yellow]")
        elif isinstance(results_data, str):
            # Handle string result when parse_chunks_to_string is False but a string was returned anyway
            console.print("\n[bold magenta]--- Results String ---[/bold magenta]")
            console.print(results_data)
        elif results_data: # It's a pager object
            if args.content_search_spec_type == "chunks":
                console.print("\n[bold magenta]--- Individual Chunks ---[/bold magenta]")
                chunk_count = 0
                try:
                    # Iterate through the pager returned by get_chunks
                    for page in results_data.pages:
                        if not hasattr(page, 'results') or not page.results: continue
                        for result in page.results:
                            # Ensure the result structure is as expected by get_chunks
                            if hasattr(result, 'chunk'):
                                chunk_count += 1
                                console.print(f"\n[bold]Chunk {chunk_count}:[/bold]")
                                # Use the client's formatter if available
                                console.print(client.chunk_format(result.chunk))
                            elif hasattr(result, 'document') and hasattr(result.document, 'chunks'):
                                # Fallback if structure is different (e.g., document with chunks)
                                for chunk in result.document.chunks:
                                        chunk_count += 1
                                        console.print(f"\n[bold]Chunk {chunk_count} (from doc {result.document.id}):[/bold]")
                                        console.print(f"  Content: {getattr(chunk, 'content', 'N/A')}")
                                        console.print(f"  Doc Name: {getattr(chunk, 'document_metadata', {}).get('name', 'N/A')}") 
                    if chunk_count == 0:
                        console.print("[yellow]No chunks found in the results.[/yellow]")

                except Exception as page_err:
                    console.print(f"[bold red]Error processing search results pager: {page_err}[/bold red]")
                    console.print(f"[red]{traceback.format_exc()}[/red]")
            elif args.content_search_spec_type == "documents":
                console.print("\n[bold magenta]--- Individual Documents ---[/bold magenta]")
                doc_count = 0
                try:
                    # Iterate through the pager returned by get_documents
                    for page in results_data.pages:
                        if not hasattr(page, 'results') or not page.results: continue
                        for result in page.results:
                            if hasattr(result, 'document'):
                                doc_count += 1
                                console.print(f"\n[bold]Document {doc_count}:[/bold]")
                                console.print(client.document_format(result.document))
                    
                    if doc_count == 0:
                        console.print("[yellow]No documents found in the results.[/yellow]")
                except Exception as page_err:
                    console.print(f"[bold red]Error processing document results: {page_err}[/bold red]")
                    console.print(f"[red]{traceback.format_exc()}[/red]")
        else:
            console.print("[yellow]No results found or error occurred.[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error during data store search: {e}[/bold red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")


def search_by_id_and_or_date_command(args):
    """Handles the `discovery-engine search-by-id-and-or-date` subcommand (Data Store Chunks)."""
    console.print(f"[cyan]Searching data store '{args.data_store_id}' by ID/Date for query: '{args.query}' (mode: chunks)[/cyan]")
    # Similar implementation to search_command, but calls search_by_objectId_and_or_date
    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            data_store_id=args.data_store_id, # Target datastore
            location=args.location
        )
        results_data = client.search_by_objectId_and_or_date(
            query=args.query,
            objectId=args.object_id,
            date=args.date,
            # num_previous_chunks=args.num_previous_chunks, # Pass these through
            # num_next_chunks=args.num_next_chunks, # Pass these through
            page_size=args.page_size,
            parse_chunks_to_string=args.parse_chunks_to_string,
            serving_config=args.serving_config,
            data_store_ids=args.data_store_ids
        )

        # Output processing identical to search_command
        if args.parse_chunks_to_string:
            console.print("\n[bold magenta]--- Combined Chunk String (Filtered) ---[/bold magenta]")
            console.print(results_data if results_data else "[yellow]No results found or error occurred.[/yellow]")
        elif results_data:
            console.print("\n[bold magenta]--- Individual Chunks (Filtered) ---[/bold magenta]")
            chunk_count = 0
            try:
                 # Iterate through the pager returned by get_chunks
                 for page in results_data.pages:
                     if not hasattr(page, 'results') or not page.results: continue
                     for result in page.results:
                          # Ensure the result structure is as expected by get_chunks
                          if hasattr(result, 'chunk'):
                               chunk_count += 1
                               console.print(f"\n[bold]Chunk {chunk_count}:[/bold]")
                               # Use the client's formatter if available
                               console.print(client.chunk_format(result.chunk))
                          elif hasattr(result, 'document') and hasattr(result.document, 'chunks'):
                               # Fallback if structure is different (e.g., document with chunks)
                               for chunk in result.document.chunks:
                                    chunk_count += 1
                                    console.print(f"\n[bold]Chunk {chunk_count} (from doc {result.document.id}):[/bold]")
                                    console.print(f"  Content: {getattr(chunk, 'content', 'N/A')}")
                                    console.print(f"  Doc Name: {getattr(chunk, 'document_metadata', {}).get('name', 'N/A')}") # Example access

                 if chunk_count == 0:
                     console.print("[yellow]No chunks found in the filtered results.[/yellow]")
            except Exception as page_err:
                 console.print(f"[bold red]Error processing filtered search results pager: {page_err}[/bold red]")
        else:
            console.print("[yellow]No results found or error occurred.[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error during filtered data store search: {e}[/bold red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")


# --- NEW Search Engine Command ---
def search_engine_command(args):
    """Handles the `discovery-engine search-engine` subcommand."""
    if not _DISCOVERYENGINE_AVAILABLE:
        console.print("[bold red]Error: google-cloud-discoveryengine library is required but not installed.[/bold red]")
        return

    console.print(f"[cyan]Searching engine '{args.engine_id}' for query: '{args.query}'[/cyan]")

    try:
        client = DiscoveryEngineClient(
            project_id=args.project,
            engine_id=args.engine_id,
            location=args.location
        )

        # --- Map CLI string args to Enums ---
        query_expansion_map = {
            "AUTO": discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
            "DISABLED": discoveryengine.SearchRequest.QueryExpansionSpec.Condition.DISABLED,
        }
        spell_correction_map = {
            "AUTO": discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO,
            "SUGGEST": discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.SUGGESTION_ONLY,
        }

        query_expansion_level = query_expansion_map.get(args.query_expansion, discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO)
        spell_correction_mode = spell_correction_map.get(args.spell_correction, discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO)

        # --- Call the search_engine method ---
        pager = client.search_engine(
            search_query=args.query,
            engine_id=args.engine_id,
            serving_config_id=args.serving_config_id,
            collection_id=args.collection_id,
            page_size=args.page_size,
            return_snippet=args.return_snippet,
            summary_result_count=args.summary_count,
            include_citations=args.include_citations,
            custom_prompt=args.custom_prompt,
            model_version=args.model_version,
            query_expansion_level=query_expansion_level,
            spell_correction_mode=spell_correction_mode,
            filter_str=args.filter,
            user_pseudo_id=args.user_id,
            # boost_spec, params, custom_fine_tuning_spec could be added here if parsed from args
        )

        # --- Process and Print Results ---
        if pager:
            console.print("\n[bold magenta]--- Search Engine Results ---[/bold magenta]")
            results_found_on_any_page = False
            page_num = 0
            try:
                for page in pager.pages:
                    page_num += 1
                    results_found_on_this_page = False
                    console.print(f"\n[bold]--- Page {page_num} ---[/bold]")

                    # Print Summary (available on the page level)
                    if hasattr(page, 'summary') and page.summary and page.summary.summary_text:
                        results_found_on_any_page = True
                        results_found_on_this_page = True
                        console.print("\n[bold green]Search Summary:[/bold green]")
                        console.print(page.summary.summary_text)
                        if args.include_citations and hasattr(page.summary, 'summary_with_metadata') and page.summary.summary_with_metadata:
                            citation_metadata = page.summary.summary_with_metadata.citation_metadata
                            if citation_metadata and hasattr(citation_metadata, 'citations'):
                                # Get the actual list of Citation objects
                                citation_list = citation_metadata.citations
                                console.print("[bold cyan]Citations:[/bold cyan]")
                                for i, citation in enumerate(citation_list):
                                    # citation is now a Citation object with start_index, end_index, sources
                                    source_details = []
                                    # Check if the citation has sources and iterate through them
                                    if hasattr(citation, 'sources') and citation.sources:
                                        for source in citation.sources:
                                            # source is a CitationSource object with reference_index
                                            ref_idx = getattr(source, 'reference_index', 'N/A')
                                            source_details.append(f"RefIdx:{ref_idx+1}") # Append details of each source

                                    source_info = ", ".join(source_details) if source_details else "No Source Info"
                                    start_idx = getattr(citation, 'start_index', 'N/A')
                                    end_idx = getattr(citation, 'end_index', 'N/A')
                                    console.print(f"  Citation {i+1}: Segment [{start_idx}-{end_idx}], Sources [{source_info}]")

                            references = page.summary.summary_with_metadata.references
                            if references:
                                console.print("[bold cyan]References:[/bold cyan]")
                                for i, ref in enumerate(references):
                                    console.print(f"  - {i+1} {ref}")

                        console.print("-" * 20)

                    # Print Document Results (available on the page level)
                    if hasattr(page, 'results') and page.results:
                        console.print(f"[bold blue]Documents Found ({len(page.results)} on this page):[/bold blue]")
                        for i, result in enumerate(page.results):
                            results_found_on_any_page = True
                            results_found_on_this_page = True
                            console.print(f"\n[bold]Result {i+1}:[/bold]")
                            doc = result.document
                            console.print(f"  ID: {doc.id}")
                            # Display structData if present
                            if doc.struct_data:
                                try:
                                    struct_dict = convert_composite_to_native(doc.struct_data)
                                    metadata_output = struct_dict.get("structData", {})
                                    title = struct_dict.get("title", "")
                                    content = struct_dict.get("content", "")
                                    console.print(f"  Title: {title}")
                                    console.print(f"  Content: {content}")
                                except Exception as json_err:
                                    console.print(f"[yellow]  Warning: Could not convert metadata Struct to JSON: {json_err}[/yellow]")
                                    metadata_output = doc.struct_data
                            console.print(f"  Metadata: {json.dumps(metadata_output, indent=2)}")
                            # Display Snippets if requested and available
                            if args.return_snippet and 'snippets' in doc.derived_struct_data:
                                   console.print("[bold cyan]  Snippets:[/bold cyan]")
                                   for snippet in doc.derived_struct_data['snippets']:
                                        console.print(f"    - {snippet.get('snippet', 'N/A').strip()}") # Adjust key if needed
                            elif args.return_snippet:
                                   console.print("[yellow]  (Snippets requested but not found in result)[/yellow]")
                            console.print("-" * 5)
                        
                        console.print("-" * 20) # End of results list for page

                    if not results_found_on_this_page:
                         console.print("[yellow](No summary or document results on this page)[/yellow]")


                if not results_found_on_any_page:
                    console.print("[yellow]No results found for the search query.[/yellow]")

            except Exception as page_err:
                 console.print(f"[bold red]Error processing results pager: {page_err}[/bold red]")
                 console.print(f"[red]{traceback.format_exc()}[/red]")

        else:
            console.print("[yellow]Search call did not return a result object (check logs for errors).[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error during engine search: {e}[/bold red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")


# --- Argparse Setup ---

def setup_discovery_engine_subparser(subparsers):
    """
    Sets up the `discovery-engine` subparser and its subcommands.
    """
    discovery_engine_parser = subparsers.add_parser('discovery-engine', help='Interact with Google Cloud Discovery Engine')
    # Add arguments common to most discovery engine commands
    discovery_engine_parser.add_argument('--project', required=True, help='Google Cloud project ID')
    discovery_engine_parser.add_argument('--location', default='global', help='Location (e.g., global, us, eu)')
    # data_store_id is required by many commands, make it common if possible, else add per-command
    # For simplicity here, adding it per command where needed or as a specific arg for client init

    discovery_engine_subparsers = discovery_engine_parser.add_subparsers(dest='subcommand', required=True, title='Discovery Engine Subcommands')

    # --- Create Datastore subcommand ---
    create_datastore_parser = discovery_engine_subparsers.add_parser('create-datastore', help='Create a new Discovery Engine datastore')
    create_datastore_parser.add_argument('--data-store-id', required=True, help='The ID for the new datastore')
    create_datastore_parser.add_argument('--type', choices=['chunk'], default='chunk', help='The type of datastore (currently only chunk)')
    create_datastore_parser.add_argument('--chunk-size', type=int, default=500, help='Chunk size for layout-based chunking (100-500)')
    create_datastore_parser.add_argument('--collection', default='default_collection', help='Collection ID')
    create_datastore_parser.set_defaults(func=discovery_engine_command)

    # --- Import Documents subcommand ---
    import_documents_parser = discovery_engine_subparsers.add_parser('import-documents', help='Import documents into a datastore')
    import_documents_parser.add_argument('--data-store-id', required=True, help='The ID of the target datastore')
    import_grp = import_documents_parser.add_mutually_exclusive_group(required=True)
    import_grp.add_argument('--gcs-uri', help='GCS URI of documents (gs://bucket/...) or pattern (gs://bucket/*.json)')
    import_grp.add_argument('--bigquery-source', nargs=2, metavar=('DATASET_ID', 'TABLE_ID'), help='BigQuery dataset and table ID')
    import_documents_parser.add_argument('--data-schema', default='content', help='Data schema (content, document, custom, csv, user_event)')
    import_documents_parser.add_argument('--branch', default='default_branch', help='Target branch')
    import_documents_parser.add_argument('--bigquery-project-id', help='Project ID for BigQuery source (defaults to --project)')
    import_documents_parser.set_defaults(func=discovery_engine_command)

    # --- Import Documents with Metadata (JSONL) subcommand ---
    import_docs_meta_parser = discovery_engine_subparsers.add_parser('import-documents-with-metadata', help='Import documents via JSONL metadata file')
    import_docs_meta_parser.add_argument('--data-store-id', required=True, help='The ID of the target datastore')
    import_docs_meta_parser.add_argument('--gcs-uri', required=True, help='GCS URI of the JSONL metadata file')
    import_docs_meta_parser.add_argument('--branch', default='default_branch', help='Target branch')
    # data_schema might not be needed if using inline source via metadata file
    # import_docs_meta_parser.add_argument('--data-schema', default='content', help='Data schema')
    import_docs_meta_parser.set_defaults(func=discovery_engine_command)

    # --- Import Single Document with Metadata subcommand ---
    import_doc_meta_parser = discovery_engine_subparsers.add_parser('import-document-with-metadata', help='Import a single document with metadata')
    import_doc_meta_parser.add_argument('--data-store-id', required=True, help='The ID of the target datastore')
    import_doc_meta_parser.add_argument('--gcs-uri', required=True, help='GCS URI of the document content')
    meta_grp = import_doc_meta_parser.add_mutually_exclusive_group(required=True)
    meta_grp.add_argument('--metadata-file', help='Path to a local JSON file containing metadata')
    meta_grp.add_argument('--metadata-string', help='JSON string containing metadata')
    import_doc_meta_parser.add_argument('--branch', default='default_branch', help='Target branch')
    import_doc_meta_parser.set_defaults(func=discovery_engine_command)

    # --- Search Data Store (Chunks/Documents) subcommand ---
    search_parser = discovery_engine_subparsers.add_parser('search', help='Search a datastore (fetches chunks or documents)')
    search_parser.add_argument('--query', required=True, help='The search query')
    search_parser.add_argument('--data-store-id', required=True, help='Data store ID to search')
    search_parser.add_argument('--page-size', type=int, default=10, help='Max results per page')
    search_parser.add_argument('--parse-chunks-to-string', action='store_true', help='Output results as one formatted string. Only applicable for "chunks"')
    search_parser.add_argument('--serving-config', default='default_config', help='Serving config ID for the data store')
    search_parser.add_argument('--content_search_spec_type', default="chunks", help='"chunks" or "documents" depending on data store type')
    search_parser.add_argument('--filter', help='filter for the search')


    # Add arguments for num_previous_chunks, num_next_chunks, data_store_ids if needed
    # search_parser.add_argument('--num-previous-chunks', type=int, default=3)
    # search_parser.add_argument('--num-next-chunks', type=int, default=3)
    # search_parser.add_argument('--data-store-ids', nargs='+', help='Search across multiple data stores')
    search_parser.set_defaults(func=discovery_engine_command)

    # --- Search Data Store By ID/Date (Chunks) subcommand ---
    search_by_id_parser = discovery_engine_subparsers.add_parser('search-by-id-and-or-date', help='Search a datastore by ID/date (fetches chunks)')
    search_by_id_parser.add_argument('--query', required=True, help='The search query')
    search_by_id_parser.add_argument('--data-store-id', required=True, help='Data store ID to search')
    search_by_id_parser.add_argument('--object-id', help='Object ID to filter by (exact match)')
    search_by_id_parser.add_argument('--date', help='Date filter (YYYY-MM-DDTHH:MM:SSZ or similar ISO format)')
    search_by_id_parser.add_argument('--page-size', type=int, default=10, help='Max results per page')
    search_by_id_parser.add_argument('--parse-chunks-to-string', action='store_true', help='Output results as one formatted string')
    search_by_id_parser.add_argument('--serving-config', default='default_config', help='Serving config ID')
    search_by_id_parser.add_argument('--content_search_spec_type', default="chunks", help='"chunks" or "documents" depending on data store type')

    # Add arguments for num_previous_chunks, num_next_chunks, data_store_ids if needed
    # search_by_id_parser.add_argument('--num-previous-chunks', type=int, default=3)
    # search_by_id_parser.add_argument('--num-next-chunks', type=int, default=3)
    search_by_id_parser.add_argument('--data-store-ids', nargs='+', help='Search across multiple data stores (optional)')
    search_by_id_parser.set_defaults(func=discovery_engine_command)

    # --- NEW: Search Engine subcommand ---
    search_engine_parser = discovery_engine_subparsers.add_parser('search-engine', help='Search a Discovery Engine (fetches documents/summary)')
    search_engine_parser.add_argument('--query', required=True, help='The search query')
    search_engine_parser.add_argument('--engine-id', required=True, help='Engine ID to search')
    search_engine_parser.add_argument('--serving-config-id', default='default_config', help='Serving config ID for the engine')
    search_engine_parser.add_argument('--collection-id', default='default_collection', help='Collection ID for the engine path')
    search_engine_parser.add_argument('--page-size', type=int, default=10, help='Max results per page')
    search_engine_parser.add_argument('--no-snippet', action='store_false', dest='return_snippet', help='Disable fetching snippets')
    search_engine_parser.add_argument('--summary-count', type=int, default=5, help='Number of results for summary (0 to disable)')
    search_engine_parser.add_argument('--no-citations', action='store_false', dest='include_citations', help='Disable citations in summary')
    search_engine_parser.add_argument('--custom-prompt', help='Custom preamble for summary generation')
    search_engine_parser.add_argument('--model-version', default='stable', help='Summary model version')
    search_engine_parser.add_argument('--query-expansion', choices=['AUTO', 'DISABLED'], default='AUTO', help='Query expansion level')
    search_engine_parser.add_argument('--spell-correction', choices=['AUTO', 'SUGGEST'], default='AUTO', help='Spell correction mode')
    search_engine_parser.add_argument('--filter', help='Filter string to apply')
    search_engine_parser.add_argument('--user-id', help='User pseudo ID for personalization/analytics')
    search_engine_parser.set_defaults(func=discovery_engine_command)

    # Add other subparsers for create-engine, etc. if needed
