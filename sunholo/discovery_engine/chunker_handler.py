from ..logging import log
from ..utils.config import load_config_key
from ..utils.gcp_project import get_gcp_project
from ..components import load_memories

from .discovery_engine_client import DiscoveryEngineClient
from .create_new import create_new_discovery_engine
    

def do_discovery_engine(message_data, metadata, vector_name):
    """

    Example:
    ```python
    message_data = "gs://bucket_name/path_to_file.txt"
    metadata = {"user": "admin"}
    vector_name = "example_vector"
    response = do_discovery_engine(message_data, metadata, vector_name)
    print(response)
    # Imported file to corpus: {'status': 'success'}
    ```
    """

    memories = load_memories(vector_name)
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
                    data_store_id=vector_name, 
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
                    log.info(f"Attempting to create a new DiscoveryEngine corpus: {vector_name}")
                    try:
                        new_corp = create_new_discovery_engine(vector_name)
                    except Exception as err:
                        log.error(f"Failed to create new DiscoveryEngine {vector_name} - {str(err)}")
                        continue
                    if new_corp:
                        log.info(f"Found new DiscoveryEngine {vector_name=} - {new_corp=}")
                        response = corp.import_documents(
                            gcs_uri=message_data
                        )
                    
                continue

        metadata["source"] = message_data
        return metadata
    
    else:
        log.warning("Only gs:// data is supported for Discovery Engine")


def check_discovery_engine_in_memory(vector_name):
    memories = load_config_key("memory", vector_name=vector_name, kind="vacConfig")
    for memory in memories:  # Iterate over the list
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore:
                if vectorstore == "discovery_engine" or vectorstore == "vertex_ai_search":
                    log.info(f"Found vectorstore {vectorstore}")
                    return True
    
    return False

def discovery_engine_chunker_check(message_data, metadata, vector_name):
    # discovery engine handles its own chunking/embedding
    memories = load_config_key("memory", vector_name=vector_name, kind="vacConfig")
    total_memories = len(memories)
    llama = None
    if check_discovery_engine_in_memory(vector_name):
        llama = do_discovery_engine(message_data, metadata, vector_name)
        log.info(f"Processed discovery engine: {llama}")

    # If discovery engine is the only entry, return
    if llama and total_memories == 1:

        return llama
    
    elif llama:
        log.info("Discovery Engine found but not the only memory, continuing with other processes.")

        return None