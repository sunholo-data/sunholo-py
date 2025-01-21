from ..utils import load_config_key
from ..custom_logging import log

def can_agent_stream(agent_name: str):

    log.debug(f"agent_type: {agent_name} checking streaming...")
    endpoints_config = load_config_key(agent_name, "dummy_value", kind="agentConfig")
    post_endpoints = endpoints_config['post']
    
    return 'stream' in post_endpoints

    
    