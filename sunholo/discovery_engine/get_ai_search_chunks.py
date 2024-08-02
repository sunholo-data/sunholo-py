from ..utils import ConfigManager
from ..utils.gcp_project  import get_gcp_project
from ..custom_logging import log
from .discovery_engine_client import DiscoveryEngineClient
from ..components import load_memories

def get_all_chunks(question:str, config:ConfigManager):
    """
    Look through a config memory key and find all Vertex AI Search retrievers, call them and return a joined string of chunks

        args: question - question to search similarity for
        config: A ConfigManager object

        returns: a big string of chunks
    """
    memories = load_memories(config=config)
    chunks = []

    if not memories:
        return None

    vector_name = config.vector_name
    for memory in memories:
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore == "discovery_engine" or vectorstore == "vertex_ai_search":
                if value.get('read_only'):
                    new_vector_name = value.get('vector_name')
                    if not new_vector_name:
                        log.warning("read_only specified but no new vector_name to read from")
                    vector_name = new_vector_name
                
                num_chunks = value.get('num_chunks') or 3

                chunk = get_chunks(question, vector_name, num_chunks)
                if chunk:
                    chunks.append(chunk)
    if chunks:
        return "\n".join(chunks)

    log.warning(f"No chunks found for {vector_name}")
    return None

def get_chunks(question, vector_name, num_chunks):
    de = DiscoveryEngineClient(vector_name, project_id=get_gcp_project(include_config=True))
    try:
        return de.get_chunks(question, num_previous_chunks=num_chunks, num_next_chunks=num_chunks)
    except Exception as err:
        log.error(f"No discovery engine chunks found: {str(err)}")
    


