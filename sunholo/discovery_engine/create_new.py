from .discovery_engine_client import DiscoveryEngineClient
from ..utils.config import load_config_key

def create_new_discovery_engine(vector_name):
    gcp_config = load_config_key("gcp_config", vector_name=vector_name, kind="vacConfig")

    chunker_config = load_config_key("chunker", vector_name=vector_name, kind="vacConfig")

    project_id = gcp_config.get('project_id')
    #location = gcp_config.get('location')

    de = DiscoveryEngineClient(
                    data_store_id=vector_name, 
                    project_id=project_id,
                    # location needs to be 'eu' or 'us' which doesn't work with other configurations
                    #location=location
                    )

    new_store = de.create_data_store(chunk_size=chunker_config.get("chunk_size"))

    return new_store