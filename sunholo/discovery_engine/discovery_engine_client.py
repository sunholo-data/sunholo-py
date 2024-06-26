try:
    from google.api_core.client_options import ClientOptions
    from google.cloud import discoveryengine_v1alpha as discoveryengine
except ImportError:
    ClientOptions = None
    discoveryengine = None

from ..logging import log
from typing import Optional

class DiscoveryEngineClient:
    """
    Client for interacting with Google Cloud Discovery Engine.

    Args:
        project_id (str): Your Google Cloud project ID.
        data_store_id (str): The ID of your Discovery Engine data store.
        location (str, optional): The location of the data store (default is 'eu').

    Example:
        ```python
        client = DiscoveryEngineClient(project_id='your-project-id', data_store_id='your-data-store-id')

        # Create a collection
        collection_name = client.create_collection("my_new_collection")

        # Perform a search
        search_response = client.get_chunks("your query", "your_collection_id")

        ```

        Parsing:
        ```python
        # Perform a search
        search_response = client.get_chunks("your query", "your_collection_id")

        # Iterate through the search results
        for result in search_response.results:
            # Get the document (which contains the chunks)
            document = result.document

            # Iterate through the chunks within the document
            for chunk in document.chunks:
                chunk_text = chunk.snippet  # Extract the text content of the chunk
                chunk_document_name = chunk.document_name  # Get the name of the document the chunk belongs to
                
                # Do something with the chunk_text and chunk_document_name (e.g., print, store, etc.)
                print(f"Chunk Text: {chunk_text}")
                print(f"Document Name: {chunk_document_name}")
        ```
    """
    def __init__(self, data_store_id, project_id, location="eu"):
        if not discoveryengine:
            raise ImportError("Google Cloud Discovery Engine not available, install via `pip install sunholo[gcp]`")

        self.project_id = project_id
        self.data_store_id = data_store_id
        self.location = location
        client_options = (
            ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
            if location != "global"
            else None
        )
        self.client = discoveryengine.DataStoreServiceClient(client_options=client_options)
        self.parent = self.client.branch_path(
            project=project_id,
            location=location,
            data_store=data_store_id,
            branch="default_branch",
        )

    def create_data_store(
        self, chunk_size: int = 500
    ) -> str:
        """
        Creates a new data store with default configuration.

        Args:
            chunk_size (int, optional): The size of the chunks to create for documents (default is 500).

        Returns:
            str: The name of the long-running operation for data store creation.
        """

        # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1alpha.types.DocumentProcessingConfig
        doc_config = discoveryengine.DocumentProcessingConfig(
            chunking_config=discoveryengine.DocumentProcessingConfig.ChunkingConfig(
                layout_based_chunking_config=discoveryengine.DocumentProcessingConfig.ChunkingConfig.LayoutBasedChunkingConfig(
                    chunk_size=chunk_size,
                    include_ancestor_headings=True
                )
            ),
            default_parsing_config=discoveryengine.DocumentProcessingConfig.ParsingConfig(
                layout_parsing_config=discoveryengine.DocumentProcessingConfig.ParsingConfig.LayoutParsingConfig()
            )
        )

        # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.services.data_store_service.DataStoreServiceClient
        # https://cloud.google.com/python/docs/reference/discoveryengine/0.11.4/google.cloud.discoveryengine_v1alpha.types.DataStore
        data_store = discoveryengine.DataStore(
            display_name=self.data_store_id,
            # Options: GENERIC, MEDIA, HEALTHCARE_FHIR
            industry_vertical=discoveryengine.IndustryVertical.GENERIC,
            # Options: SOLUTION_TYPE_RECOMMENDATION, SOLUTION_TYPE_SEARCH, SOLUTION_TYPE_CHAT, SOLUTION_TYPE_GENERATIVE_CHAT
            solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
            # Options: NO_CONTENT, CONTENT_REQUIRED, PUBLIC_WEBSITE
            content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
            # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.DocumentProcessingConfig
            document_processing_config=doc_config
        )

        # https://cloud.google.com/python/docs/reference/discoveryengine/0.11.4/google.cloud.discoveryengine_v1alpha.types.CreateDataStoreRequest
        request = discoveryengine.CreateDataStoreRequest(
            parent=self.parent,
            data_store_id=self.data_store_id,
            data_store=data_store,
            # Optional: For Advanced Site Search Only
            # create_advanced_site_search=True,
        )

        # Make the request
        operation = self.client.create_data_store(request=request)

        log.info(f"Waiting for operation to complete: {operation.operation.name}")
        response = operation.result()

        # Once the operation is complete,
        # get information from operation metadata
        metadata = discoveryengine.CreateDataStoreMetadata(operation.metadata)

        # Handle the response
        log.info(f"{response=} {metadata=}")

        return operation.operation.name

    def get_chunks(
        self,
        query: str,
        num_previous_chunks: int = 3,
        num_next_chunks: int = 3,
        page_size: int = 10,
        doc_or_chunks: str = "CHUNKS",  # or DOCUMENTS
    ):
        """Retrieves chunks or documents based on a query.

        Args:
            query (str): The search query.
            collection_id (str): The ID of the collection to search.
            num_previous_chunks (int, optional): Number of previous chunks to return for context (default is 3).
            num_next_chunks (int, optional): Number of next chunks to return for context (default is 3).
            page_size (int, optional): The maximum number of results to return per page (default is 10).

        Returns:
            discoveryengine.SearchResponse: The search response object containing the search results.

        Example:
            ```python
            search_response = client.get_chunks('your query', 'your_collection_id')
            for result in search_response.results:
                for chunk in result.document.chunks:
                    print(f"Chunk: {chunk.snippet}, document name: {chunk.document_name}")
            ```
        """
        serving_config = self.client.get_default_serving_config(
            name=self.client.serving_config_path(
                project=self.project_id, 
                location=self.location, 
                data_store=self.data_store_id, 
                serving_config="default_serving_config")
                ).name
        
        search_request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=page_size, 
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                #snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                #    return_snippet=True
                #),
                search_result_mode=doc_or_chunks,  # CHUNKS or DOCUMENTS
                chunk_spec=discoveryengine.SearchRequest.ContentSearchSpec.ChunkSpec(
                    num_previous_chunks=num_previous_chunks,
                    num_next_chunks=num_next_chunks,
                ),
            ),
        )

        search_response = self.client.search(search_request)

        return search_response

    def import_documents(self,
        gcs_uri: Optional[str] = None,
        data_schema="content",
        bigquery_dataset: Optional[str] = None,
        bigquery_table: Optional[str] = None,
        bigquery_project_id: Optional[str] = None,
    ) -> str:
        """
        Args:
        - gcs_uri: Required. List of Cloud Storage URIs to input files. Each URI can be up to 2000 characters long. URIs can match the full object path (for example, gs://bucket/directory/object.json) or a pattern matching one or more files, such as gs://bucket/directory/*.json. A request can contain at most 100 files (or 100,000 files if data_schema is content). Each file can be up to 2 GB (or 100 MB if data_schema is content). 
        - data_schema: Must be one of 'user_event', 'custom' or 'document' if using BigQuery. Default 'content' only for GCS. The schema to use when parsing the data from the source. Supported values for document imports: - document (default): One JSON Document per line. Each document must have a valid Document.id. - content: Unstructured data (e.g. PDF, HTML). Each file matched by input_uris becomes a document, with the ID set to the first 128 bits of SHA256(URI) encoded as a hex string. - custom: One custom data JSON per row in arbitrary format that conforms to the defined Schema of the data store. This can only be used by the GENERIC Data Store vertical. - csv: A CSV file with header conforming to the defined Schema of the data store. Each entry after the header is imported as a Document. This can only be used by the GENERIC Data Store vertical. Supported values for user event imports: - user_event (default): One JSON UserEvent per line. 
        
        """

        if gcs_uri:
            request = discoveryengine.ImportDocumentsRequest(
                parent=self.parent,
                # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1alpha.types.GcsSource
                gcs_source=discoveryengine.GcsSource(
                    input_uris=[gcs_uri], data_schema=data_schema,
                ),
                # Options: `FULL`, `INCREMENTAL`
                reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
            )
        else:
            request = discoveryengine.ImportDocumentsRequest(
                parent=self.parent,
                bigquery_source=discoveryengine.BigQuerySource(
                    project_id=bigquery_project_id or self.project_id,
                    dataset_id=bigquery_dataset,
                    table_id=bigquery_table,
                    data_schema=data_schema,
                ),
                # Options: `FULL`, `INCREMENTAL`
                reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
            )

        # Make the request
        operation = self.client.import_documents(request=request)

        log.info(f"Waiting for operation to complete: {operation.operation.name}")
        response = operation.result()

        # Once the operation is complete,
        # get information from operation metadata
        metadata = discoveryengine.ImportDocumentsMetadata(operation.metadata)

        # Handle the response
        log.info(f"{response=} {metadata=}")

        return operation.operation.name

