from ..custom_logging import log
from typing import Optional, List, Dict, Any

import asyncio
import json
import uuid
from ..utils.mime import guess_mime_type
import traceback

_DISCOVERYENGINE_AVAILABLE = False
try:
    from google.api_core.client_options import ClientOptions
    from google.cloud import discoveryengine
    from google.api_core.retry import Retry, if_exception_type
    from google.api_core.exceptions import ResourceExhausted, AlreadyExists
    from google.api_core.exceptions import GoogleAPIError
    from google.cloud.discoveryengine_v1 import SearchResponse, Chunk
    from google.cloud.discoveryengine_v1.services.search_service.pagers import SearchPager, SearchAsyncPager
    _DISCOVERYENGINE_AVAILABLE = True
except ImportError:
    ClientOptions = None
    discoveryengine = None
    Chunk = None
    SearchResponse = None
    SearchAsyncPager = None
    SearchPager = None


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
    def __init__(self, data_store_id=None, engine_id=None, project_id=None, location="eu"):
        if not discoveryengine:
            raise ImportError("Google Cloud Discovery Engine not available, install via `pip install sunholo[gcp]`")
        
        if project_id is None:
            raise ValueError("Must specify project_id")
        
        if data_store_id is None and engine_id is None:
            raise ValueError("Must specify at least one of data_store_id or engine_id")

        self.project_id = project_id
        self.data_store_id = data_store_id
        self.engine_id = engine_id
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
        # Initialize the async client only if there's an active event loop
        try:
            asyncio.get_running_loop()
            self.async_search_client = discoveryengine.SearchServiceAsyncClient(client_options=client_options)
        except RuntimeError:
            # No event loop in non-async environment, set async client to None
            log.info("No event loop detected; skipping Discoveryengine async client initialization")
            self.async_search_client = None
        
        log.info(f"Discovery Engine client initialized with {self.project_id=}, {self.data_store_id=}, {self.location=}")

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

    def _search_data_store_path(self, 
                                data_store_id: str, 
                                collection_id: str = "default_collection", 
                                serving_config: str = "default_serving_config"):
        if data_store_id.startswith("projects/"):
            return data_store_id  # Already a full path
        
        return f"projects/{self.project_id}/locations/{self.location}/collections/{collection_id}/dataStores/{data_store_id}"
        
    def get_chunks(
        self,
        query: str,
        num_previous_chunks: int = 3,
        num_next_chunks: int = 3,
        page_size: int = 10,
        parse_chunks_to_string: bool = True,
        serving_config: str = "default_serving_config",
        data_store_ids: Optional[List[str]] = None,
        filter_str:str=None
    ):
        """Retrieves chunks or documents based on a query.

        Args:
            query (str): The search query.
            num_previous_chunks (int, optional): Number of previous chunks to return for context (default is 3).
            num_next_chunks (int, optional): Number of next chunks to return for context (default is 3).
            page_size (int, optional): The maximum number of results to return per page (default is 10).
            parse_chunks_to_string: If True will put chunks in one big string, False will return object
            serving_config: The resource name of the Search serving config 
            data_store_ids: If you want to search over many data stores, not just the one that was used to init the class.
                            They should be of the format projects/{project}/locations/{location}/collections/{collection_id}/dataStores/{data_store_id}

        Returns:
            discoveryengine.SearchResponse or str: The search response object or string of chunks.

        Example:
            ```python
            search_response = client.get_chunks('your query', 'your_collection_id')
            for result in search_response.results:
                for chunk in result.document.chunks:
                    print(f"Chunk: {chunk.snippet}, document name: {chunk.document_name}")
            ```
        """

        return self.search_with_filters(
            query=query,
            filter_str=filter_str,
            num_previous_chunks=num_previous_chunks,
            num_next_chunks=num_next_chunks,
            page_size=page_size,
            parse_chunks_to_string=parse_chunks_to_string,
            serving_config=serving_config,
            data_store_ids=data_store_ids,
            content_search_spec_type="chunks"
        )

    async def async_get_chunks(
        self,
        query: str,
        num_previous_chunks: int = 3,
        num_next_chunks: int = 3,
        page_size: int = 10,
        parse_chunks_to_string: bool = True,
        serving_config: str = "default_serving_config",
        data_store_ids: Optional[List[str]] = None,
        filter_str:str=None
    ):
        """Asynchronously retrieves chunks or documents based on a query.

        Args:
            query (str): The search query.
            num_previous_chunks (int, optional): Number of previous chunks to return for context (default is 3).
            num_next_chunks (int, optional): Number of next chunks to return for context (default is 3).
            page_size (int, optional): The maximum number of results to return per page (default is 10).
            parse_chunks_to_string: If True will put chunks in one big string, False will return object
            serving_config: The resource name of the Search serving config 
            data_store_ids: If you want to search over many data stores, not just the one that was used to init the class.
                            They should be of the format projects/{project}/locations/{location}/collections/{collection_id}/dataStores/{data_store_id}

        Returns:
            discoveryengine.SearchResponse or str: The search response object or string of chunks.
        """
        # Use async_search_with_filters with filter_str=None to perform a regular search
        return await self.async_search_with_filters(
            query=query,
            filter_str=filter_str,
            num_previous_chunks=num_previous_chunks,
            num_next_chunks=num_next_chunks,
            page_size=page_size,
            parse_chunks_to_string=parse_chunks_to_string,
            serving_config=serving_config,
            data_store_ids=data_store_ids
        )
    
    def chunk_format(self, chunk):

        return (
                    f"# {chunk.id}\n"
                    f"{chunk.content}\n"
                    f"## {chunk.id} metadata\n"
                    f"Relevance score: {chunk.relevance_score}\n"
                    f"Document URI: {chunk.document_metadata.uri}\n"
                    f"Document Title: {chunk.document_metadata.title}\n"
                    f"Document Metadata: {dict(chunk.document_metadata.struct_data)}\n"
                )        

    def process_chunks(self, response):
        all_chunks = []

        # Check if the response contains results
        if not hasattr(response, 'results') or not response.results:
            log.info(f'No results found in response: {response=}')
            return []
        
        # Iterate through each result in the response
        for result in response.results:
            if hasattr(result, 'chunk'):      
                chunk = result.chunk
                chunk_metadata = chunk.ChunkMetadata
            else:
                log.warning("No chunk found in result")

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

    async def async_process_chunks(self, response):
        all_chunks = []

        # Check if the response contains results
        if not hasattr(response, 'results') or not response.results:
            log.info(f'No results found in response: {response=}')
            return []
        
        # Iterate through each result in the response
        for result in response.results:
            if hasattr(result, 'chunk'):      
                chunk = result.chunk
                chunk_metadata = chunk.ChunkMetadata
            else:
                log.warning("No chunk found in result")

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

    def get_documents(
        self,
        query: str,
        page_size: int = 10,
        parse_documents_to_string: bool = True,
        serving_config: str = "default_serving_config",
        data_store_ids: Optional[List[str]] = None,
        filter_str:str=None,
        max_limit:int=None
    ):
        """Retrieves entire documents based on a query.

        Args:
            query (str): The search query.
            page_size (int, optional): The maximum number of results to return per page (default is 10).
            parse_documents_to_string: If True will put documents in one big string, False will return object
            serving_config: The resource name of the Search serving config 
            data_store_ids: If you want to search over many data stores, not just the one that was used to init the class.
                            They should be of the format projects/{project}/locations/{location}/collections/{collection_id}/dataStores/{data_store_id}

        Returns:
            discoveryengine.SearchResponse or str: The search response object or string of documents.

        Example:
            ```python
            search_response = client.get_documents('your query')
            for result in search_response.results:
                doc = result.document
                print(f"Document: {doc.name}, Title: {doc.derived_struct_data.get('title')}")
            ```
        """
        # Use search_with_filters with content_search_spec_type="documents" to get documents instead of chunks
        return self.search_with_filters(
            query=query,
            filter_str=filter_str,
            page_size=page_size,
            parse_chunks_to_string=parse_documents_to_string,
            serving_config=serving_config,
            data_store_ids=data_store_ids,
            content_search_spec_type="documents",
            max_limit=max_limit
        )

    async def async_get_documents(
        self,
        query: str,
        page_size: int = 10,
        parse_documents_to_string: bool = True,
        serving_config: str = "default_serving_config",
        data_store_ids: Optional[List[str]] = None,
        filter_str:str=None,
        max_limit:int=None

    ):
        """Asynchronously retrieves entire documents based on a query.

        Args:
            query (str): The search query.
            page_size (int, optional): The maximum number of results to return per page (default is 10).
            parse_documents_to_string: If True will put documents in one big string, False will return object
            serving_config: The resource name of the Search serving config 
            data_store_ids: If you want to search over many data stores, not just the one that was used to init the class.
                            They should be of the format projects/{project}/locations/{location}/collections/{collection_id}/dataStores/{data_store_id}

        Returns:
            discoveryengine.SearchResponse or str: The search response object or string of documents.
        """
        # Note: You'll need to update async_search_with_filters to handle content_search_spec_type
        # as it doesn't currently have that parameter
        return await self.async_search_with_filters(
            query=query,
            filter_str=filter_str,
            page_size=page_size,
            parse_chunks_to_string=parse_documents_to_string, 
            serving_config=serving_config,
            data_store_ids=data_store_ids,
            content_search_spec_type="documents",
            max_limit=max_limit

        )

    def document_format(self, document):
        """Format a document for string output."""
        # Extract useful fields from the document

        document_id = document.id
        document_name = document.name
        
        # Get content if available
        content = ""
        if hasattr(document, 'content') and document.content:
            if hasattr(document.content, 'uri') and document.content.uri:
                content = f"Content URI: {document.content.uri}\n"
            if hasattr(document.content, 'mime_type') and document.content.mime_type:
                content += f"Content Type: {document.content.mime_type}\n"
        
        # Get structured data if available
        struct_data = ""
        if hasattr(document, 'struct_data') and document.struct_data:
            struct_data = f"Structured Data: {dict(document.struct_data)}\n"
        
        # Get derived structured data if available
        derived_data = ""
        if hasattr(document, 'derived_struct_data') and document.derived_struct_data:
            derived_data = f"Derived Data: {dict(document.derived_struct_data)}\n"
        
        # Return formatted document string
        return (
            f"# Document: {document_id}\n"
            f"Resource Name: {document_name}\n"
            f"{content}"
            f"{struct_data}"
            f"{derived_data}"
        )

    def process_documents(self, response, max_limit:int=None):
        """Process a search response containing documents into a formatted string."""
        all_documents = []
        result_count = 0
        
        # Check if the response contains results
        if not response or not hasattr(response, 'results') or not response.results:
            log.info(f'No results found in response: {response=}')
            return []
        
        # Simpler approach: Just process the direct results from the response
        # This handles the case where it's just a simple SearchResponse
        for result in response.results:
            if hasattr(result, 'document'):
                document = result.document
                all_documents.append(self.document_format(document))
                result_count += 1
                
                # Check if we've reached max_limit
                if max_limit is not None and result_count >= max_limit:
                    log.info(f"Reached max_limit of {max_limit} results, stopping processing")
                    break
            else:
                log.warning("No document found in result")
        
        # If there are pages, check gently without assuming too much about the structure
        # Only process if we haven't already hit the max_limit
        if (max_limit is None or result_count < max_limit) and hasattr(response, 'pages'):
            try:
                # For each page (after the first which we've already processed)
                for page in list(response.pages)[1:]:  # Skip first page as we already processed it
                    if hasattr(page, 'results'):
                        for result in page.results:
                            if hasattr(result, 'document'):
                                document = result.document
                                all_documents.append(self.document_format(document))
                                result_count += 1
                                
                                # Check if we've reached max_limit
                                if max_limit is not None and result_count >= max_limit:
                                    log.info(f"Reached max_limit of {max_limit} results while processing pages")
                                    break
                            else:
                                log.warning("No document found in result during page processing")
                        
                        # Break out of the page loop if we've reached max_limit
                        if max_limit is not None and result_count >= max_limit:
                            break
            except Exception as e:
                # Don't let page iteration issues break the whole function
                log.warning(f"Error during page iteration, proceeding with results already collected: {e}")
        
        # Combine all documents into one long string
        result_string = "\n\n".join(all_documents)
        
        return result_string

    async def async_process_documents(self, response, max_limit:int=None):
        """Process a search response containing documents into a formatted string asynchronously."""
        all_documents = []
        result_count = 0

        # Check if the response contains results
        if not response or not hasattr(response, 'results') or not response.results:
            log.info(f'No results found in response: {response=}')
            return []

        # Simpler approach: Just process the direct results from the response
        # This handles the case where it's just a simple SearchResponse
        for result in response.results:
            if hasattr(result, 'document'):
                document = result.document
                all_documents.append(self.document_format(document))
                result_count += 1
                
                # Check if we've reached max_limit
                if max_limit is not None and result_count >= max_limit:
                    log.info(f"Reached max_limit of {max_limit} results, stopping processing")
                    break
            else:
                log.warning("No document found in result")
        
        # If there are pages, check gently without assuming too much about the structure
        # Only process if we haven't already hit the max_limit
        if (max_limit is None or result_count < max_limit) and hasattr(response, 'pages'):
            try:
                # Since pages is an async iterator, we need special handling
                first_page = True  # Flag to skip first page (already processed above)
                async for page in response.pages:
                    if first_page:
                        first_page = False
                        continue  # Skip first page as we already processed it
                        
                    if hasattr(page, 'results'):
                        for result in page.results:
                            if hasattr(result, 'document'):
                                document = result.document
                                all_documents.append(self.document_format(document))
                                result_count += 1
                                
                                # Check if we've reached max_limit
                                if max_limit is not None and result_count >= max_limit:
                                    log.info(f"Reached max_limit of {max_limit} results while processing pages")
                                    break
                            else:
                                log.warning("No document found in result during page processing")
                        
                        # Break out of the page loop if we've reached max_limit
                        if max_limit is not None and result_count >= max_limit:
                            break
            except Exception as e:
                # Don't let page iteration issues break the whole function
                log.warning(f"Error during async page iteration, proceeding with results already collected: {e}")
        
        # Combine all documents into one long string
        result_string = "\n\n".join(all_documents)
        
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
            self.engine_id = engine_id
            return engine_id
        
        log.info(f"Waiting for create vertex ai search operation to complete: {operation.operation.name}")
        response = operation.result()

        # Once the operation is complete,
        # get information from operation metadata
        metadata = discoveryengine.CreateEngineMetadata(operation.metadata)

        # Handle the response
        log.info(f"{response=} {metadata=}")
        self.engine_id = engine_id
        return operation.operation.name

    def _import_document_request(self,
        request
    ) -> str:
        """
        Handles the common logic for making an ImportDocumentsRequest, including retrying.

        Args:
            request (discoveryengine.ImportDocumentsRequest): The prepared request object.

        Returns:
            str: The operation name.
        """
        @self.my_retry()
        def import_documents_with_retry(doc_client, request):
            return doc_client.import_documents(request=request)
        
        try:
            log.debug(f"Requesting import of documents: {request=}")
            operation = import_documents_with_retry(self.doc_client, request)
        except ResourceExhausted as e:
            log.error(f"DiscoveryEngine Operation failed after retries due to quota exceeded: {e}")
            raise e
        except AlreadyExists as e:
            # Extract relevant info from the request to log
            gcs_uri = request.gcs_source.input_uris if request.gcs_source else None
            bigquery_table = request.bigquery_source.table_id if request.bigquery_source else None
            log.warning(f"DiscoveryEngine - Already exists: {e} - {gcs_uri=} {bigquery_table=}")
        except Exception as e:
            log.error(f"An unexpected DiscoveryEngine error occurred: {e}")
            raise e

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
        return self._import_document_request(request)


    def import_documents_with_metadata(self, gcs_uri: str, data_schema="content", branch="default_branch"):
        """
        Supply a JSONLD GCS location to import all the GS URIs within and their metadata
        """
        parent = self.doc_client.branch_path(
            self.project_id, 
            self.location, 
            self.data_store_id, 
            branch
        )

        # 1. Prepare your documents with metadata:
        documents_with_metadata = []
        with open(gcs_uri, 'r') as f:  # Assuming one JSON object per line in your GCS file
            for line in f:
                try:
                    document_data = json.loads(line)  # Load the JSON from the line
                    # Check if it has the required fields, if not create them
                    if "id" not in document_data:
                        document_data["id"] = str(uuid.uuid4())
                    if "structData" not in document_data:
                        document_data["structData"] = {}
                    if "content" not in document_data:
                        document_data["content"] = {}
                    # Create the Document object with your metadata
                    document = discoveryengine.Document(
                        name = f"{parent}/documents/{document_data['id']}", # important!
                        id=document_data["id"],
                        struct_data=document_data.get("structData", {}),  # Your metadata here
                        content = discoveryengine.Content(
                            mime_type = document_data.get("content", {}).get("mimeType", "text/plain"),
                            uri = document_data.get("content", {}).get("uri", ""),
                        )
                    )

                    if "jsonData" in document_data:
                        document.json_data = document_data["jsonData"]

                    documents_with_metadata.append(document)

                except json.JSONDecodeError as e:
                    log.error(f"Error decoding JSON in line: {line.strip()}. Error: {e}")
                    continue  # Skip to the next line if there's an error
                except Exception as e:
                    log.error(f"Unknown error: {str(e)}")
                    raise e

        # 2. Use InlineSource to import:
        request = discoveryengine.ImportDocumentsRequest(
            parent=parent,
            inline_source=discoveryengine.ImportDocumentsRequest.InlineSource(
                documents=documents_with_metadata,  # Pass the list of Document objects
            ),
            reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
        )

        log.debug(f"Making import_document_request: {request}")
        return self._import_document_request(request)

    def _create_unique_gsuri_docid(self, gcs_uri:str):
        import hashlib
        # Create SHA-256 hash of the URI
        hash_object = hashlib.sha256(gcs_uri.encode())
        # Take first 16 bytes (128 bits) and encode as hex
        return hash_object.hexdigest()[:32]
    
    def import_document_with_metadata(self, gcs_uri: str, metadata: dict, branch="default_branch"):
        """
        Imports a single document with metadata.

        Args:
            gcs_uri: The GCS URI of the document to import.
            metadata: A dictionary containing the metadata for the document.
            branch: The branch to import the document into.

        Returns:
            str: The operation name.
        """
        try:
            log.info(f"Importing doc with metadata: {gcs_uri=}, {metadata=}")
            # 1. Generate a unique document ID
            document_id = self._create_unique_gsuri_docid(gcs_uri)

            # 2. Create a Document object
            parent = self.doc_client.branch_path(
                self.project_id, self.location, self.data_store_id, branch
            )
            document = discoveryengine.Document(
                name=f"{parent}/documents/{document_id}",
                id=document_id,
                struct_data=metadata,
                content=discoveryengine.Document.Content(
                    uri=gcs_uri,
                    mime_type=self.get_mime_type(gcs_uri)
                )
            )

            # 3. Use InlineSource for import
            request = discoveryengine.ImportDocumentsRequest(
                parent=parent,
                inline_source=discoveryengine.ImportDocumentsRequest.InlineSource(
                    documents=[document],
                ),
                reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
            )

            # 4. Make the import request (using the common method)
            return self._import_document_request(request)

        except Exception as e:
            log.error(f"Error importing document with metadata: {e} {traceback.format_exc()}")
            raise e
    
    def get_mime_type(self, uri:str):
        return guess_mime_type(uri)
    
    def search_with_filters(self, query, filter_str=None,
                        num_previous_chunks=3, num_next_chunks=3, 
                        page_size=10, parse_chunks_to_string=True, 
                        serving_config="default_serving_config",
                        data_store_ids: Optional[List[str]] = None,
                        content_search_spec_type="chunks",
                        max_limit=None):
        """
        Searches with a generic filter string.

        Args:
            query (str): The search query.
            filter_str (str, optional): The filter string to apply (e.g., "source LIKE 'my_source' AND eventTime > TIMESTAMP('2024-01-01')").
            #... other parameters from get_chunks

        Returns:
            discoveryengine.SearchResponse or str: The search response object or string of chunks.
        """
        if max_limit is not None and max_limit < page_size:
            page_size = max_limit

        serving_config_path = self.search_client.serving_config_path(
            self.project_id,
            self.location,
            self.data_store_id,
            serving_config
        )

        if content_search_spec_type == "chunks":
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                            search_result_mode="CHUNKS", 
                            chunk_spec=discoveryengine.SearchRequest.ContentSearchSpec.ChunkSpec(
                                num_previous_chunks=num_previous_chunks,
                                num_next_chunks=num_next_chunks,
                            ),
                        )
        elif content_search_spec_type == "documents":
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                            search_result_mode="DOCUMENTS"
                            )
        else:
            raise ValueError(f"Unknown content_search_spec_type={content_search_spec_type}")

        search_request = discoveryengine.SearchRequest(
            serving_config=serving_config_path,
            query=query,
            page_size=page_size, 
            content_search_spec=content_search_spec,
            filter=filter_str # name:'ANY("king kong")'
        )

        if data_store_ids:
            search_request.data_store_specs = [
                discoveryengine.SearchRequest.DataStoreSpec(
                    data_store=self._search_data_store_path(data_store_id, serving_config=serving_config)
                )
                for data_store_id in data_store_ids
            ]



        log.info(f"Discovery engine request with filter: {search_request=}")
        try:
            search_response = self.search_client.search(search_request)
        except Exception as e:
            log.info(f"No results {search_request.data_store_specs=}: {str(e)}")
            return None
        
        if parse_chunks_to_string:
            if content_search_spec_type=="chunks":
                if parse_chunks_to_string:
                    big_string = self.process_chunks(search_response)
                    log.info(f"Discovery engine chunks string sample: {big_string[:100]}")

                    return big_string
                
            elif content_search_spec_type=="documents":
                big_string = self.process_documents(search_response, max_limit=max_limit)
                log.info(f"Discovery engine documents string sample: {big_string[:100]}")

                return big_string
        
        log.info("Discovery engine response object")

        return search_response

    async def async_search_with_filters(self, query, filter_str=None,
                            num_previous_chunks=3, num_next_chunks=3, 
                            page_size=10, parse_chunks_to_string=True, 
                            serving_config="default_serving_config",
                            data_store_ids: Optional[List[str]] = None,
                            content_search_spec_type="chunks",
                            max_limit=None):
        """
        Searches with a generic filter string asynchronously.

        Args:
            query (str): The search query.
            filter_str (str, optional): The filter string to apply (e.g., "source LIKE 'my_source' AND eventTime > TIMESTAMP('2024-01-01')").
            #... other parameters from get_chunks

        Returns:
            discoveryengine.SearchResponse or str: The search response object or string of chunks.
        """
        if max_limit is not None and max_limit < page_size:
            page_size = max_limit

        serving_config_path = self.async_search_client.serving_config_path(
            self.project_id,
            self.location,
            self.data_store_id,
            serving_config
        )

        if content_search_spec_type == "chunks":
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                            search_result_mode="CHUNKS", 
                            chunk_spec=discoveryengine.SearchRequest.ContentSearchSpec.ChunkSpec(
                                num_previous_chunks=num_previous_chunks,
                                num_next_chunks=num_next_chunks,
                            ),
                        )
        elif content_search_spec_type == "documents":
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                            search_result_mode="DOCUMENTS"
                            )
        else:
            raise ValueError(f"Unknown content_search_spec_type={content_search_spec_type}")

        search_request = discoveryengine.SearchRequest(
            serving_config=serving_config_path,
            query=query,
            page_size=page_size, 
            content_search_spec=content_search_spec,
            filter=filter_str # name:'ANY("king kong")'
        )

        if data_store_ids:
            search_request.data_store_specs = [
                discoveryengine.SearchRequest.DataStoreSpec(
                    data_store=self._search_data_store_path(data_store_id, serving_config=serving_config)
                )
                for data_store_id in data_store_ids
            ]

        log.info(f"Discovery engine request with filter: {search_request=}")
        try:
            search_response = await self.async_search_client.search(search_request)
        except Exception as e:
            log.info(f"No results {search_request.data_store_specs=}: {str(e)}")
            return None
            
        if parse_chunks_to_string:
            if content_search_spec_type=="chunks":
                if parse_chunks_to_string:
                    big_string = await self.async_process_chunks(search_response)
                    log.info(f"Discovery engine chunks string sample: {big_string[:100]}")

                    return big_string
                
            elif content_search_spec_type=="documents":
                big_string = await self.async_process_documents(search_response, max_limit=max_limit)
                log.info(f"Discovery engine documents string sample: {big_string[:100]}")

                return big_string
        
        log.info("Discovery engine response object")
        
        return search_response

    def search_by_objectId_and_or_date(self, query, objectId=None, date=None, **kwargs):
        """
        Searches and filters by objectId (exact match) and/or date.

        Args:
            query (str): The search query.
            objectId (str, optional): The exact objectId to filter by.
            date (str, optional): The literal_iso_8601_datetime_format date to filter by e.g. 2025-02-24T12:25:30.123Z
            **kwargs: Additional keyword arguments to pass to `search_with_filters`.

        Returns:
            list: A list of search results.
        """
        filter_clauses = []
        if objectId:
            filter_clauses.append(f'objectId: ANY("{objectId}")')
        if date:
            filter_clauses.append(f'eventTime >= "{date}"')

        if filter_clauses:
            filter_str = " AND ".join(filter_clauses)  # Combine with AND
            return self.search_with_filters(query, filter_str, **kwargs)
        else:
            # No filters, perform regular search
            return self.search_with_filters(query, **kwargs)

    async def async_search_by_objectId_and_or_date(self, query, objectId=None, date=None, **kwargs):
        """
        Searches and filters by objectId (exact match) and/or date asynchronously.

        Args:
            query (str): The search query.
            objectId (str, optional): The exact objectId to filter by.
            date (str, optional): The literal_iso_8601_datetime_format date to filter by e.g. 2025-02-24T12:25:30.123Z
            **kwargs: Additional keyword arguments to pass to `async_search_with_filters`.

        Returns:
            list: A list of search results.
        """
        filter_clauses = []
        if objectId:
            filter_clauses.append(f'objectId: ANY("{objectId}")')
        if date:
            filter_clauses.append(f'eventTime >= "{date}"')

        if filter_clauses:
            filter_str = " AND ".join(filter_clauses)  # Combine with AND
            return await self.async_search_with_filters(query, filter_str, **kwargs)
        else:
            # No filters, perform regular search
            return await self.async_search_with_filters(query, **kwargs)

    # --- NEW ENGINE SEARCH METHODS ---
    def search_engine(
        self,
        search_query: str,
        engine_id: str = None,
        serving_config_id: str = "default_config",
        page_size: int = 10,
        return_snippet: bool = True,
        summary_result_count: int = 5,
        include_citations: bool = True,
        custom_prompt: Optional[str] = None,
        model_version: str = "stable",
        query_expansion_level: "discoveryengine.SearchRequest.QueryExpansionSpec.Condition" # type: ignore
             # Default value assignment MUST be conditional
             = discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO if _DISCOVERYENGINE_AVAILABLE else None,

        spell_correction_mode: "discoveryengine.SearchRequest.SpellCorrectionSpec.Mode" # type: ignore
             # Default value assignment MUST be conditional
             = discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO if _DISCOVERYENGINE_AVAILABLE else None,
        filter_str: Optional[str] = None,
        boost_spec: Optional["discoveryengine.SearchRequest.BoostSpec"] = None, # Okay if default is None # type: ignore
        params: Optional[Dict[str, Any]] = None,
        user_pseudo_id: Optional[str] = None,
        collection_id: str = "default_collection" # Needed for engine path
    ):
        """
        Performs a search against a specified Discovery Engine Search Engine.

        Allows configuration for snippets, summaries, query expansion, spell correction, etc.

        Args:
            search_query: The user's search query string.
            engine_id: The ID of the search engine to query or uses class engine_id it init with.
            serving_config_id: The ID of the specific serving config for the engine.
            page_size: Maximum number of results per page.
            return_snippet: Whether to request snippets in the results.
            summary_result_count: Number of results to use for generating a summary.
                                  Set to 0 to disable summaries.
            include_citations: Whether summaries should include citations.
            custom_prompt: A custom preamble text to guide the summary generation model.
            model_version: The version of the summary generation model (e.g., "stable").
            query_expansion_level: Level of query expansion to apply (AUTO, DISABLED).
            spell_correction_mode: Mode for spell correction (AUTO, SUGGEST).
            filter_str: An optional filter string to apply to the search.
            boost_spec: Optional boost specification object.
            params: Optional dictionary of custom parameters.
            user_pseudo_id: Optional unique identifier for the user/session.
            custom_fine_tuning_spec: Optional spec to use a fine-tuned model.
            collection_id: The collection ID associated with the engine.

        Returns:
            A SearchPager object to iterate through results, or None if an error occurs.
        
        Example:
        client = DiscoveryEngineClient(
            project_id=PROJECT_ID,
            data_store_id=DATA_STORE_ID,
            location=LOCATION
        )

        # --- Example: Searching an Engine ---
        search_query_engine = "tell me about search engines"
        log.info(f"\n--- Searching Engine: {ENGINE_ID} ---")
        engine_pager = client.search_engine(
            search_query=search_query_engine,
            engine_id=ENGINE_ID,
            summary_result_count=3 # Request a summary for 3 results
        )

        if engine_pager:
            results_found = False
            # Iterate through pages to get summary/results
            for page in engine_pager.pages:
                 results_found = True
                 if page.summary:
                      print(f"\nSearch Summary:\n{page.summary.summary_text}\n")
                      # Citations are part of the summary object if requested
                      if page.summary.summary_with_metadata:
                           print("Summary Metadata/Citations:")
                           for citation in page.summary.summary_with_metadata.citations:
                                print(f"  - Citation Source: {citation.sources}")
                           # Access references etc. if needed

                 print("Results on this page:")
                 for result in page.results:
                      print(f"  ID: {result.document.id}")
                      print(f"  Name: {result.document.name}")
                      # Access snippet if available in result.document.derived_struct_data['snippets']
                      # Access other document fields as needed (struct_data, etc.)
                      # print(f"  Raw Result: {result}") # For detailed inspection
                 print("-" * 10)

            if not results_found:
                 print("No results found for the engine search.")
        else:
            print(f"Engine search failed for query: '{search_query_engine}'")

        """

        if not _DISCOVERYENGINE_AVAILABLE:
            log.error("Discovery Engine library not available at runtime.")
            return None
        
        if engine_id:
            self.engine_id = engine_id
        
        if engine_id is None and self.engine_id is None:
            raise ValueError("Could not find self.engine_id")
        
        
        try:
            # Construct the serving config path for an ENGINE
            # Note: The client library path helper is for data stores/serving configs within them.
            # We need the path for an engine's serving config.
            serving_config_path = (
                f"projects/{self.project_id}/locations/{self.location}/"
                f"collections/{collection_id}/engines/{self.engine_id}/"
                f"servingConfigs/{serving_config_id}"
            )
            log.info(f"Using Engine Serving Config Path: {serving_config_path}")

            # --- Build ContentSearchSpec ---
            snippet_spec = None
            if return_snippet:
                snippet_spec = discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True
                )

            summary_spec = None
            if summary_result_count > 0:
                model_prompt_spec = None
                if custom_prompt:
                    model_prompt_spec = discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                        preamble=custom_prompt
                    )

                summary_spec = discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=summary_result_count,
                    include_citations=include_citations,
                    ignore_adversarial_query=True,  # Default from original sample
                    ignore_non_summary_seeking_query=True, # Default from original sample
                    model_prompt_spec=model_prompt_spec,
                    model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                        version=model_version
                    ),
                )

            content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=snippet_spec,
                summary_spec=summary_spec,
                # Unlike get_chunks, don't specify search_result_mode or chunk_spec here
                # unless specifically needed for a document/snippet search use case.
            )

            # --- Build other Specs ---
            query_expansion_spec = discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=query_expansion_level
            )

            spell_correction_spec = discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=spell_correction_mode
            )

            # --- Build SearchRequest ---
            request = discoveryengine.SearchRequest(
                serving_config=serving_config_path,
                query=search_query,
                page_size=page_size,
                content_search_spec=content_search_spec,
                query_expansion_spec=query_expansion_spec,
                spell_correction_spec=spell_correction_spec,
                filter=filter_str,
                boost_spec=boost_spec,
                params=params,
                user_pseudo_id=user_pseudo_id,
                # Add other relevant fields like facet_specs if needed
            )

            log.info(f"Searching engine '{self.engine_id}' with request: {request}")
            response_pager = self.search_client.search(request)
            log.info(f"Search successful for query '{search_query}' against engine '{self.engine_id}'.")
            return response_pager

        except GoogleAPIError as e:
            log.error(f"API error searching engine '{self.engine_id}': {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error searching engine '{self.engine_id}': {e}\n{traceback.format_exc()}")
            return None

    async def async_search_engine(
        self,
        search_query: str,
        engine_id: str=None,
        serving_config_id: str = "default_config",
        page_size: int = 10,
        return_snippet: bool = True,
        summary_result_count: int = 5,
        include_citations: bool = True,
        custom_prompt: Optional[str] = None,
        model_version: str = "stable",
        query_expansion_level: "discoveryengine.SearchRequest.QueryExpansionSpec.Condition" # type: ignore
             # Default value assignment MUST be conditional
             = discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO if _DISCOVERYENGINE_AVAILABLE else None,

        spell_correction_mode: "discoveryengine.SearchRequest.SpellCorrectionSpec.Mode" # type: ignore
             # Default value assignment MUST be conditional
             = discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO if _DISCOVERYENGINE_AVAILABLE else None,
        filter_str: Optional[str] = None,
        boost_spec: Optional["discoveryengine.SearchRequest.BoostSpec"] = None, # Okay if default is None # type: ignore
        params: Optional[Dict[str, Any]] = None,
        user_pseudo_id: Optional[str] = None,
        collection_id: str = "default_collection"
    ):
        """
        Performs an asynchronous search against a specified Discovery Engine Search Engine.

        Allows configuration for snippets, summaries, query expansion, spell correction, etc.

        Args:
            (Same arguments as the synchronous search_engine method)

        Returns:
            An SearchAsyncPager object to iterate through results asynchronously,
            or None if an error occurs or the async client is not available.
        """
        if engine_id:
            self.engine_id = engine_id
        
        if engine_id is None and self.engine_id is None:
            raise ValueError("Could not find self.engine_id")
        
        if not self.async_search_client:
             log.error("Cannot call async_search_engine: Async client not initialized.")
             raise RuntimeError("Async client not initialized. Ensure class is instantiated within an async context.")

        try:
            # Construct the serving config path for an ENGINE (same as sync)
            serving_config_path = (
                f"projects/{self.project_id}/locations/{self.location}/"
                f"collections/{collection_id}/engines/{self.engine_id}/"
                f"servingConfigs/{serving_config_id}"
            )
            log.info(f"Using Async Engine Serving Config Path: {serving_config_path}")

            # --- Build Specs (same logic as sync version) ---
            snippet_spec = None
            if return_snippet:
                snippet_spec = discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(...)
            summary_spec = None
            if summary_result_count > 0:
                model_prompt_spec = None
                if custom_prompt:
                    model_prompt_spec = discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                        preamble=custom_prompt
                    )
                summary_spec = discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=summary_result_count,
                    include_citations=include_citations,
                    ignore_adversarial_query=True,  # Default from original sample
                    ignore_non_summary_seeking_query=True, # Default from original sample
                    model_prompt_spec=model_prompt_spec,
                    model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                        version=model_version
                    ),
                )

            content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=snippet_spec,
                summary_spec=summary_spec,
            )
            query_expansion_spec = discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=query_expansion_level
            )

            spell_correction_spec = discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=spell_correction_mode
            )

            # --- Build SearchRequest (same logic as sync version) ---
            request = discoveryengine.SearchRequest(
                serving_config=serving_config_path,
                query=search_query,
                page_size=page_size,
                content_search_spec=content_search_spec,
                query_expansion_spec=query_expansion_spec,
                spell_correction_spec=spell_correction_spec,
                filter=filter_str,
                boost_spec=boost_spec,
                params=params,
                user_pseudo_id=user_pseudo_id,
            )

            log.info(f"Async searching engine '{self.engine_id}' with request: {request}")
            response_pager = await self.async_search_client.search(request)
            log.info(f"Async search successful for query '{search_query}' against engine '{self.engine_id}'.")
            return response_pager

        except GoogleAPIError as e:
            log.error(f"Async API error searching engine '{self.engine_id}': {e}")
            return None
        except Exception as e:
            log.error(f"Async unexpected error searching engine '{self.engine_id}': {e}\n{traceback.format_exc()}")
            return None

# --- End of DiscoveryEngineClient class ---