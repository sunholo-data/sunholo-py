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
from ..logging import setup_logging

logging = setup_logging()

from ..utils import load_config_key, load_config

def route_qna(vector_name):

    agent_type = load_config_key('agent', vector_name, filename='config/llm_config.yaml')
    logging.info(f'agent_type: {agent_type}')

    agent_route, _ = load_config('config/cloud_run_urls.json')
    logging.info(f'agent_route: {agent_route}')

    try:
        agent_url = agent_route[agent_type]
    except KeyError:
        raise ValueError(f'agent_url not found for {agent_type}')
    
    logging.info(f'agent_url: {agent_url}')
    return agent_url

def route_endpoint(vector_name):

    agent_type = load_config_key('agent', vector_name, filename='config/llm_config.yaml')

    stem = route_qna(vector_name)

    agent_config, _ = load_config('config/agent_config.yaml')

    # Select the appropriate configuration based on agent_type
    if agent_type in agent_config:
        endpoints_config = agent_config[agent_type]
    else:
        endpoints_config = agent_config['default']

    # Replace placeholders in the config
    endpoints = {}
    for key, value in endpoints_config.items():
        format_args = {'stem': stem}
        if '{vector_name}' in value and vector_name is not None:
            format_args['vector_name'] = vector_name
        endpoints[key] = value.format(**format_args)

    return endpoints

