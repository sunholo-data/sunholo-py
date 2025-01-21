try:
    from vertexai.preview import rag
except ImportError:
    rag = None

from ..custom_logging import log
from ..utils import ConfigManager
from ..vertex import init_vertex
from .get_files import fetch_corpus
from .llamaindex_class import LlamaIndexVertexCorpusManager
from ..components import load_memories

    

def do_llamaindex(message_data, metadata, vector_name):
    """
    Configures and manages the corpus for a VertexAI project using the specified vector name
    by importing message data from Google Cloud Storage or Google Drive URLs.

    This function loads configuration from a YAML file, initializes a Vertex AI environment,
    and either fetches an existing corpus or creates a new one if it doesn't exist.
    It supports importing files directly from cloud storage links.

    Parameters:
        message_data (str): The URL to the data on Google Cloud Storage or Google Drive that needs to be imported to the corpus.
        metadata (dict): Additional metadata not explicitly used in this function but might be needed for extended functionality.
        vector_name (str): The name of the vector (and corpus) which will be used to locate and configure the specific settings from the configuration files.

    Raises:
        ValueError: If the necessary configurations for GCP or project ID are not found, or if the corpus could not be established.
        NotImplementedError: If the data is not from supported sources (Google Cloud Storage or Google Drive).

    Example:
    ```python
    message_data = "gs://bucket_name/path_to_file.txt"
    metadata = {"user": "admin"}
    vector_name = "example_vector"
    response = do_llamaindex(message_data, metadata, vector_name)
    print(response)
    # Imported file to corpus: {'status': 'success'}
    ```
    """
    if not rag:
        raise ValueError("Need to install vertexai module via `pip install sunholo[gcp]`")

    config = ConfigManager(vector_name)
    gcp_config = config.vacConfig("gcp_config")
    if not gcp_config:
        raise ValueError(f"Need config.{vector_name}.gcp_config to configure llamaindex on VertexAI")

    init_vertex(gcp_config)

    global_project_id = gcp_config.get('project_id')
    global_location = gcp_config.get('location')
    #global_data_store_id = gcp_config.get('data_store_id')

    memories = load_memories(vector_name)
    tools = []

    if not memories:
        return tools
    
    corpuses = []
    for memory in memories:
        for key, value in memory.items():  # Now iterate over the dictionary
            vectorstore = value.get('vectorstore')
            if vectorstore == "llamaindex":
                log.info(f"Found vectorstore {vectorstore}")
                if value.get('read_only'):
                    continue
                rag_id = value.get('rag_id')
                project_id = gcp_config.get('project_id')
                location = gcp_config.get('location')

                if rag_id:    
                    try:
                        corpus = fetch_corpus(
                            project_id=project_id or global_project_id,
                            location=location or global_location,
                            rag_id=rag_id
                        )
                    except Exception as err:
                        log.warning(f"Failed to fetch LlamaIndex corpus from rag_id: {err=}")
                        continue
                else:
                    try:
                        log.info("Using vertex llamaindex with own rag_id created via VAC name")
                        manager = LlamaIndexVertexCorpusManager(config, project_id=project_id, location=location)
                        # create or get existing:
                        corpus = manager.create_corpus(vector_name)
                    except Exception as err:
                        log.warning(f"Failed to fetch LlamaIndex corpus from display_name: {err=}")
                        continue
                
                corpuses.append(corpus)
                
    if not corpuses:
        log.info("No Vertex Llamaindex RAG corpus to import data")
        return None

    log.info(f"Found llamaindex corpus: {corpuses}")

    # native support for cloud storage and drive links
    chunker_config = config.vacConfig("chunker")
    
    if message_data.startswith("gs://") or message_data.startswith("https://drive.google.com"):
        log.info(f"rag.import_files for {message_data}")
        for corp in corpuses:
            response = rag.import_files(
                corpus_name=corp.name,
                paths=[message_data],
                chunk_size=chunker_config.get("chunk_size"),  # Optional
                chunk_overlap=chunker_config.get("overlap"),  # Optional
            )
            log.info(f"Imported file to corpus: {response} with metadata: {metadata}")

        metadata["source"] = message_data
        return metadata
    
    else:
        log.warning("Only gs:// and https://drive data is supported for llamaindex")
        

def check_llamaindex_in_memory(vector_name):
    memories = ConfigManager(vector_name).vacConfig("memory")

    for memory in memories:  # Iterate over the list
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore:
                log.info(f"Found vectorstore {vectorstore}")
                if vectorstore == "llamaindex":

                    return True
    
    return False

def llamaindex_chunker_check(message_data, metadata, vector_name):
    # llamaindex handles its own chunking/embedding
    memories = load_memories(vector_name)
    if not memories:
        return None
    
    total_memories = len(memories)
    llama = None
    if check_llamaindex_in_memory(vector_name):
        llama = do_llamaindex(message_data, metadata, vector_name)
        log.info(f"Processed llamaindex: {llama}")

    # If llamaindex is the only entry, return
    if llama and total_memories == 1:

        return llama
    
    elif llama:
        log.info("Llamaindex found but not the only memory, continuing with other processes.")

        return None