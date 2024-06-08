from ..utils import load_config_key
from ..logging import log

def can_agent_stream(agent_name: str):

    log.debug(f"agent_type: {agent_name} checking streaming...")
    endpoints_config = load_config_key(agent_name, "dummy_value", kind="agentConfig")
    
    return 'stream' in endpoints_config

    
    