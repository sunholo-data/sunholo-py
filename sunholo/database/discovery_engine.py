try:
    from google.api_core.client_options import ClientOptions
    from google.cloud import discoveryengine_v1alpha as discoveryengine
except ImportError:
    ClientOptions = None
    discoveryengine = None

from ..logging import log

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
        

    def create_collection(self, collection_id: str) -> str:
        """
        Creates a new collection within the specified data store.

        Args:
            collection_id (str): The ID of the collection to create.

        Returns:
            str: The resource name of the created collection.

        Example:
            ```python
            collection_name = client.create_collection('my_new_collection')
            `
        """

        parent = self.client.data_store_path(
            project=self.project_id, location=self.location, data_store=self.data_store_id
        )

        collection = discoveryengine.Collection(display_name=collection_id)
        request = discoveryengine.CreateCollectionRequest(
            parent=parent, collection_id=collection_id, collection=collection
        )

        operation = self.client.create_collection(request=request)
        log.info(f"Waiting for operation to complete: {operation.operation.name}")
        response = operation.result()

        return response.name

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
        parent = self.client.common_location_path(project=self.project_id, location=self.location)

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
            parent=parent,
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
        collection_id: str,
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
        
        filter = f'content_search=true AND collection_id="{collection_id}"'

        search_request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=page_size, 
            filter=filter,
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

