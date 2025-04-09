from ..custom_logging import log
from ..utils import ConfigManager
from ..utils.gcp_project import get_gcp_project
from ..components import load_memories

from .discovery_engine_client import DiscoveryEngineClient
from .create_new import create_new_discovery_engine
from ..embedder.embed_metadata import audit_metadata
import traceback

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
                    log.info(f"{vectorstore} is read only, skipping")
                    continue

                project_id = value.get("project_id")
                location = value.get("location", "eu")
                if not project_id:
                    gcp_config = config.vacConfig("gcp_config")
                    if not gcp_config:
                        project_id = get_gcp_project()
                    else:
                        project_id = gcp_config.get("project_id")

                if not project_id:
                    raise ValueError("Couldn't retrieve project_id for vertex_ai_search")        

                log.info(f"Using {project_id} and {location} for DiscoveryEngineClient")
                corpus = DiscoveryEngineClient(
                    data_store_id=config.vector_name, 
                    project_id=project_id,
                    # location needs to be 'eu' or 'us' which doesn't work with other configurations
                    location=location
                    )

                corpuses.append(corpus)
    if not corpuses:
        log.error("Could not find any Discovery Engine corpus to import data to")
        return None

    log.info(f"Found Discovery Engine / Vertex AI Search {corpuses=}")

    if message_data.startswith("gs://"):
        log.info(f"DiscoveryEngineClient.import_files for {message_data}")
        if "/pdf_parts/" in message_data:
            log.info(f"Not processing files with /pdf_parts/ - {message_data}")
            return None
        for corp in corpuses:
            try:
                
                metadata = audit_metadata(metadata, chunk_length=500)
                log.info(f"Importing {message_data} {metadata=} to {corp}")
                response = corp.import_document_with_metadata(
                    gcs_uri=message_data,
                    metadata=metadata
                )
                if response:
                    log.info(f"Imported file to corpus: {response} with metadata: {metadata}")
                else:
                    log.warning(f"Could not import {message_data} got not response")
            except Exception as err:
                log.error(f"Error importing {message_data} - {corp=} - {str(err)} {traceback.format_exc()}")

                if str(err).startswith("404"):
                    log.info(f"Attempting to create a new DiscoveryEngine corpus: {config.vector_name}")
                    try:
                        new_corp = create_new_discovery_engine(config)
                    except Exception as err:
                        log.error(f"Failed to create new DiscoveryEngine {config.vector_name} - {str(err)}")
                        continue
                    if new_corp:
                        log.info(f"Found new DiscoveryEngine {config.vector_name=} - {new_corp=}")
                        response = corp.import_document_with_metadata(
                            gcs_uri=message_data,
                            metadata=metadata
                        )
                else:
                    raise Exception(f"Error importing {message_data} - {corp=} - {str(err)}")

        metadata["source"] = message_data
        return metadata
    
    else:
        log.warning("Only gs:// data is supported for Discovery Engine")


def check_discovery_engine_in_memory(config:ConfigManager) -> int:
    memories = config.vacConfig("memory")

    discovery_engine_memories = 0
    for memory in memories:  # Iterate over the list
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore:
                if vectorstore == "discovery_engine" or vectorstore == "vertex_ai_search":
                    log.info(f"Found vectorstore {vectorstore}")
                    discovery_engine_memories += 1
    
    return discovery_engine_memories

def check_write_memories(config:ConfigManager):
    write_mem = []
    memories = config.vacConfig("memory")
    for memory in memories:
        for key, value in memory.items():
            if value and value.get('read_only'):
                continue
            write_mem.append(memory)
    
    return write_mem


def discovery_engine_chunker_check(message_data, 
                                   metadata, 
                                   vector_name:str=None, 
                                   config:ConfigManager=None,
                                   process:bool=True):

    if config is None:
        if vector_name is None:
            raise ValueError("Must provide config or vector_name")
        config = ConfigManager(vector_name=vector_name)

    # discovery engine handles its own chunking/embedding
    memories = config.vacConfig("memory")
    if not memories:
        return None
    
    total_memories = len(check_write_memories(config))
    total_discovery_memories = check_discovery_engine_in_memory(config)

    log.debug(f"{memories=} {total_memories=} {total_discovery_memories=}")
    if not process and total_memories == total_discovery_memories:
        log.info(f"Do not process discovery engine, and only memory found is discovery engine for {metadata} - stopping")
        
        return metadata

    if total_discovery_memories > 0:
        try:
            log.info(f"Process discovery engine for {metadata}")
            disc_meta = do_discovery_engine(message_data, metadata, config=config)
            if disc_meta is None:
                log.error(f"No disc_meta found for {metadata}")
            else:
                log.info(f"Processed discovery engine: {disc_meta}")
        except Exception as err:
            log.error(f"Error processing discovery engine: {str(err)} {traceback.format_exc()}")
            disc_meta = None

    # If discovery engine is the only entry, return
    if total_discovery_memories == total_memories:
        log.info(f"Process discovery engine was only type found in {metadata} - stopping")

        return disc_meta
    
    elif disc_meta:
        log.info("Discovery Engine found but not the only memory, continuing with other processes - returning None")

        return None