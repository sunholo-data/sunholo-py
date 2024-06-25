#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
from ..logging import log
from ..utils import load_config_key, load_config

def route_vac(vector_name: str) -> str :
    """
    Considers what VAC this vector_name belongs to
    """
    agent_url = load_config_key('agent_url', vector_name=vector_name, kind="vacConfig")
    if agent_url:
        log.info('agent_url found in llm_config.yaml')
        return agent_url

    agent = load_config_key('agent', vector_name, kind="vacConfig")
    log.info(f'agent_type: {agent}')

    agent_route, _ = load_config('config/cloud_run_urls.json')
    log.info(f'agent_route: {agent_route}')

    try:
        agent_url = agent_route[agent]
    except KeyError:
        raise ValueError(f'agent_url not found for {agent}')
    
    log.info(f'agent_url: {agent_url}')
    return agent_url

def route_endpoint(vector_name, method = 'post', override_endpoint=None):

    agent_type = load_config_key('agent_type', vector_name, kind="vacConfig")
    if not agent_type:
        agent_type = load_config_key('agent', vector_name, kind="vacConfig")

    stem = route_vac(vector_name) if not override_endpoint else override_endpoint
    
    agents_config = load_config_key(agent_type, vector_name, kind="agentConfig")
    
    log.info(f"agents_config: {agents_config}")
    if method not in agents_config:
        raise ValueError(f"Invalid method '{method}' for agent configuration.")

    # 'post' or 'get'
    endpoints_config = agents_config[method]

    log.info(f"endpoints_config: {endpoints_config}")
    # Replace placeholders in the config
    endpoints = {}
    for key, value in endpoints_config.items():
        format_args = {'stem': stem}
        if '{vector_name}' in value and vector_name is not None:
            format_args['vector_name'] = vector_name
        
        if not isinstance(value, str):
            log.warning('endpoint value not string? format_args: {format_args} - value: {value} - key: {key}')
            
        endpoints[key] = value.format(**format_args)

    return endpoints

