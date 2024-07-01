try:
    from google.api_core.client_options import ClientOptions
    from google.cloud import discoveryengine_v1alpha as discoveryengine
    from google.api_core.retry import Retry, if_exception_type
    from google.api_core.exceptions import ResourceExhausted, AlreadyExists
    from google.cloud.discoveryengine_v1alpha import SearchResponse, Chunk
except ImportError:
    ClientOptions = None
    discoveryengine = None
    Chunk = None
    SearchResponse = None

from ..logging import log
from typing import Optional, List

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
        self.store_client  = discoveryengine.DataStoreServiceClient(client_options=client_options)
        self.doc_client    = discoveryengine.DocumentServiceClient(client_options=client_options)
        self.search_client = discoveryengine.SearchServiceClient(client_options=client_options)
        self.engine_client = discoveryengine.EngineServiceClient(client_options=client_options)

    @classmethod
    def my_retry(cls):
        return Retry(
            initial=1.0,       # Initial delay before retrying (in seconds)
            maximum=60.0,      # Maximum delay between retries (in seconds)
            multiplier=2.0,    # Multiplier for the delay between retries
            timeout=300.0,     # Maximum total time to wait before giving up (in seconds)
            predicate=if_exception_type(ResourceExhausted)  # Retry if a ResourceExhausted error occurs
        )
    
    def data_store_path(self, collection: str = "default_collection"):
        return self.store_client.collection_path(
            project=self.project_id,
            location=self.location,
            collection=collection,
        )
    
    def create_data_store(self, type="chunk", chunk_size: int = 500, collection: str = "default_collection"):
        if type == "chunk":
            return self.create_data_store_chunk(chunk_size, collection)
        else:
            raise NotImplementedError("Not done yet - non-chunk data stores.")

    def create_data_store_chunk(
        self, chunk_size: int = 500,
        collection: str = "default_collection"
    ) -> str:
        """
        Creates a new data store with default configuration.

        Args:
            chunk_size (int, optional): The size of the chunks to create for documents (default is 500).

        Returns:
            str: The name of the long-running operation for data store creation.
        """

        if chunk_size > 500:
            chunk_size = 500
        elif chunk_size < 100:
            chunk_size = 100

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
            parent=self.data_store_path(collection),
            data_store_id=self.data_store_id,
            data_store=data_store,
            # Optional: For Advanced Site Search Only
            # create_advanced_site_search=True,
        )

        # Make the request
        operation = self.store_client.create_data_store(request=request)

        log.info(f"Waiting for datastore operation to complete: {operation.operation.name}")
        response = operation.result()
        log.info(f"Datastore operation creation complete: {response=}")

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
        parse_chunks_to_string: bool = True,
        serving_config: str = "default_serving_config",
    ):
        """Retrieves chunks or documents based on a query.

        Args:
            query (str): The search query.
            collection_id (str): The ID of the collection to search.
            num_previous_chunks (int, optional): Number of previous chunks to return for context (default is 3).
            num_next_chunks (int, optional): Number of next chunks to return for context (default is 3).
            page_size (int, optional): The maximum number of results to return per page (default is 10).
            parse_chunks_to_string: If True will put chunks in one big string, False will return object
            serving_config: The resource name of the Search serving config 

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

        serving_config_path = self.search_client.serving_config_path(
            self.project_id,
            self.location,
            self.data_store_id,
            serving_config
        )


        search_request = discoveryengine.SearchRequest(
            serving_config=serving_config_path,
            query=query,
            page_size=page_size, 
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                search_result_mode="CHUNKS", 
                chunk_spec=discoveryengine.SearchRequest.ContentSearchSpec.ChunkSpec(
                    num_previous_chunks=num_previous_chunks,
                    num_next_chunks=num_next_chunks,
                ),
            ),
        )

        log.info(f"Discovery engine request: {search_request=}")
        search_response = self.search_client.search(search_request)
        

        if parse_chunks_to_string:

            big_string = self.process_chunks(search_response)
            log.info(f"Discovery engine chunks string sample: {big_string[:100]}")

            return big_string
        
        log.info("Discovery engine response object")
        return search_response
    
    def chunk_format(self, chunk: Chunk):
        return (
                    f"# {chunk.id}\n"
                    f"{chunk.content}\n"
                    f"## metadata\n"
                    f"Document URI: {chunk.document_metadata.uri}\n"
                    f"Document Title: {chunk.document_metadata.title}\n"
                )        

    def process_chunks(self, response: SearchResponse):
        all_chunks = []

        # Check if the response contains results
        if not hasattr(response, 'results') or not response.results:
            raise ValueError(f'No results found in response: {response=}')
        
        # Iterate through each result in the response
        for result in response.results:
            chunk = result.chunk
            chunk_metadata = chunk.ChunkMetadata

            if hasattr(chunk_metadata, 'previous_chunks'):
                # Process previous chunks
                for prev_chunk in chunk_metadata.previous_chunks:
                    all_chunks.append(self.chunk_format(prev_chunk))

            all_chunks.append(self.chunk_format(chunk))

            # Process next chunks
            if hasattr(chunk_metadata, 'next_chunks'):
                for next_chunk in chunk_metadata.next_chunks:
                    all_chunks.append(self.chunk_format(next_chunk))

        # Combine all chunks into one long string
        result_string = "\n".join(all_chunks)

        return result_string
    
    def create_engine(self,
        engine_id: str, 
        data_store_ids: List[str],
        solution_type=None,
        search_tier=None,
        search_add_ons=None,
    ) -> str:
        """
        You only need this if calling Data Store via Vertex Tools.
        """
        # The full resource name of the collection
        # e.g. projects/{project}/locations/{location}/collections/default_collection
        parent = self.data_store_path()

        engine = discoveryengine.Engine(
            display_name=engine_id,
            # Options: GENERIC, MEDIA, HEALTHCARE_FHIR
            industry_vertical=discoveryengine.IndustryVertical.GENERIC,
            # Options: SOLUTION_TYPE_RECOMMENDATION, SOLUTION_TYPE_SEARCH, SOLUTION_TYPE_CHAT, SOLUTION_TYPE_GENERATIVE_CHAT
            solution_type=solution_type or discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
            # For search apps only
            search_engine_config=discoveryengine.Engine.SearchEngineConfig(
                # Options: SEARCH_TIER_STANDARD, SEARCH_TIER_ENTERPRISE
                search_tier=search_tier or discoveryengine.SearchTier.SEARCH_TIER_ENTERPRISE,
                # Options: SEARCH_ADD_ON_LLM, SEARCH_ADD_ON_UNSPECIFIED
                search_add_ons=search_add_ons or [discoveryengine.SearchAddOn.SEARCH_ADD_ON_UNSPECIFIED],
            ),
            # For generic recommendation apps only
            # similar_documents_config=discoveryengine.Engine.SimilarDocumentsEngineConfig,
            data_store_ids=data_store_ids,
        )

        request = discoveryengine.CreateEngineRequest(
            parent=parent,
            engine=engine,
            engine_id=engine_id,
        )

        # Make the request
        try:
            operation = self.engine_client.create_engine(request=request)
        except AlreadyExists as err:
            log.info(f"Engine already exists: - {str(err)}")

            return engine_id
        
        log.info(f"Waiting for create vertex ai search operation to complete: {operation.operation.name}")
        response = operation.result()

        # Once the operation is complete,
        # get information from operation metadata
        metadata = discoveryengine.CreateEngineMetadata(operation.metadata)

        # Handle the response
        log.info(f"{response=} {metadata=}")

        return operation.operation.name



    def import_documents(self,
        gcs_uri: Optional[str] = None,
        data_schema="content",
        branch="default_branch",
        bigquery_dataset: Optional[str] = None,
        bigquery_table: Optional[str] = None,
        bigquery_project_id: Optional[str] = None,
    ) -> str:
        """
        Args:
        - gcs_uri: Required. List of Cloud Storage URIs to input files. Each URI can be up to 2000 characters long. URIs can match the full object path (for example, gs://bucket/directory/object.json) or a pattern matching one or more files, such as gs://bucket/directory/*.json. A request can contain at most 100 files (or 100,000 files if data_schema is content). Each file can be up to 2 GB (or 100 MB if data_schema is content). 
        - data_schema: Must be one of 'user_event', 'custom' or 'document' if using BigQuery. Default 'content' only for GCS. The schema to use when parsing the data from the source. Supported values for document imports: - document (default): One JSON Document per line. Each document must have a valid Document.id. - content: Unstructured data (e.g. PDF, HTML). Each file matched by input_uris becomes a document, with the ID set to the first 128 bits of SHA256(URI) encoded as a hex string. - custom: One custom data JSON per row in arbitrary format that conforms to the defined Schema of the data store. This can only be used by the GENERIC Data Store vertical. - csv: A CSV file with header conforming to the defined Schema of the data store. Each entry after the header is imported as a Document. This can only be used by the GENERIC Data Store vertical. Supported values for user event imports: - user_event (default): One JSON UserEvent per line. 
        
        """

        parent = self.doc_client.branch_path(
            self.project_id, 
            self.location, 
            self.data_store_id, 
            branch
        )

        if gcs_uri:
            request = discoveryengine.ImportDocumentsRequest(
                parent=parent,
                # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1alpha.types.GcsSource
                gcs_source=discoveryengine.GcsSource(
                    input_uris=[gcs_uri], data_schema=data_schema,
                ),
                # Options: `FULL`, `INCREMENTAL`
                reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
            )
        else:
            request = discoveryengine.ImportDocumentsRequest(
                parent=parent,
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
        @self.my_retry()
        def import_documents_with_retry(doc_client, request):
            return doc_client.import_documents(request=request)
        
        try:
            operation = import_documents_with_retry(self.doc_client, request)
        except ResourceExhausted as e:
            log.error(f"DiscoveryEngine Operation failed after retries due to quota exceeded: {e}")

            raise e
        except AlreadyExists as e:
            log.warning(f"DiscoveryEngine - Already exists: {e} - {gcs_uri=} {bigquery_table=}")

        except Exception as e:
            log.error(f"An unexpected DiscoveryEngine error occurred: {e}")

            raise e

        return operation.operation.name

