from .discovery_engine_client import DiscoveryEngineClient
from ..utils import ConfigManager
from ..utils.gcp_project import get_gcp_project

def create_new_discovery_engine(config:ConfigManager):

    chunker_config = config.vacConfig("chunker")

    chunk_size = 500
    if chunker_config:
        if "chunk_size" in chunker_config:
            chunk_size = chunker_config["chunk_size"]    

    project_id = get_gcp_project()
    if not project_id:
        raise ValueError("Could not find project_id in gcp_config")
    
    #location = gcp_config.get('location')

    de = DiscoveryEngineClient(
                    data_store_id=config.vector_name, 
                    project_id=project_id,
                    # location needs to be 'eu' or 'us' which doesn't work with other configurations
                    #location=location
                    )

    new_store = de.create_data_store(chunk_size=chunk_size)

    return new_store