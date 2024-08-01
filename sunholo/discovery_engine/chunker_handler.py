from ..custom_logging import log
from ..utils import ConfigManager
from ..utils.gcp_project import get_gcp_project
from ..components import load_memories

from .discovery_engine_client import DiscoveryEngineClient
from .create_new import create_new_discovery_engine
    

def do_discovery_engine(message_data:str, metadata:dict, config:ConfigManager=None):
    """

    Example:
    ```python
    message_data = "gs://bucket_name/path_to_file.txt"
    metadata = {"user": "admin"}
    vector_name = "example_vector"
    response = do_discovery_engine(message_data, metadata, config=config)
    print(response)
    # Imported file to corpus: {'status': 'success'}
    ```
    """

    memories = load_memories(config=config)
    tools = []

    if not memories:
        return tools
    
    corpuses = []
    for memory in memories:
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore == "discovery_engine" or vectorstore == "vertex_ai_search":
                log.info(f"Found vectorstore {vectorstore}")
                if value.get('read_only'):
                    continue
                #location = gcp_config.get('location') 
                corpus = DiscoveryEngineClient(
                    data_store_id=config.vector_name, 
                    project_id=get_gcp_project(),
                    # location needs to be 'eu' or 'us' which doesn't work with other configurations
                    #location=location or global_location
                    )

                corpuses.append(corpus)
    if not corpuses:
        log.error("Could not find any Discovery Engine corpus to import data to")
        return None

    log.info(f"Found Discovery Engine / Vertex AI Search {corpuses=}")

    if message_data.startswith("gs://"):
        log.info(f"DiscoveryEngineClient.import_files for {message_data}")
        if "/pdf_parts/" in message_data:
            return None
        for corp in corpuses:
            try:
                response = corp.import_documents(
                    gcs_uri=message_data
                )
                log.info(f"Imported file to corpus: {response} with metadata: {metadata}")
            except Exception as err:
                log.error(f"Error importing {message_data} - {corp=} - {str(err)}")

                if str(err).startswith("404"):
                    log.info(f"Attempting to create a new DiscoveryEngine corpus: {config.vector_name}")
                    try:
                        new_corp = create_new_discovery_engine(config)
                    except Exception as err:
                        log.error(f"Failed to create new DiscoveryEngine {config.vector_name} - {str(err)}")
                        continue
                    if new_corp:
                        log.info(f"Found new DiscoveryEngine {config.vector_name=} - {new_corp=}")
                        response = corp.import_documents(
                            gcs_uri=message_data
                        )
                    
                continue

        metadata["source"] = message_data
        return metadata
    
    else:
        log.warning("Only gs:// data is supported for Discovery Engine")


def check_discovery_engine_in_memory(config:ConfigManager):
    memories = config.vacConfig("memory")

    for memory in memories:  # Iterate over the list
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore:
                if vectorstore == "discovery_engine" or vectorstore == "vertex_ai_search":
                    log.info(f"Found vectorstore {vectorstore}")
                    return True
    
    return False

def check_write_memories(config:ConfigManager):
    write_mem = []
    memories = config.vacConfig("memory")
    for memory in memories:
        for key, value in memory.items():
            if value.get('read_only'):
                continue
            write_mem.append(memory)
    
    return write_mem

def discovery_engine_chunker_check(message_data, metadata, vector_name:str=None, config:ConfigManager=None):

    if config is None:
        if vector_name is None:
            raise ValueError("Must provide config or vector_name")
        config = ConfigManager(vector_name=vector_name)

    # discovery engine handles its own chunking/embedding
    memories = config.vacConfig("memory")
    if not memories:
        return None
    
    total_memories = len(check_write_memories(config))
    llama = None
    if check_discovery_engine_in_memory(config):
        llama = do_discovery_engine(message_data, metadata, config=config)
        log.info(f"Processed discovery engine: {llama}")

    # If discovery engine is the only entry, return
    if llama and total_memories == 1:

        return llama
    
    elif llama:
        log.info("Discovery Engine found but not the only memory, continuing with other processes.")

        return None