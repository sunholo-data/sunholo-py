from ..logging import log
from ..utils.config import load_config_key
from ..components import load_memories

from .discovery_engine_client import DiscoveryEngineClient
    

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

    gcp_config = load_config_key("gcp_config", vector_name=vector_name, kind="vacConfig")
    if not gcp_config:
        raise ValueError(f"Need config.{vector_name}.gcp_config to configure discovery engine")

    global_project_id = gcp_config.get('project_id')
    #global_location = gcp_config.get('location')
    global_data_store_id = gcp_config.get('data_store_id')

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
                data_store_id = value.get('data_store_id')
                project_id = gcp_config.get('project_id')
                #location = gcp_config.get('location') 
                corpus = DiscoveryEngineClient(
                    data_store_id=data_store_id or global_data_store_id, 
                    project_id=project_id or global_project_id,
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
        for corp in corpuses:
            try:
                response = corp.import_documents(
                    gcs_uri=message_data
                )
                log.info(f"Imported file to corpus: {response} with metadata: {metadata}")
            except Exception as err:
                log.error(f"Error importing {message_data} - {corp=} - {str(err)}")
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