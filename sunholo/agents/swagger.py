import copy
from ..utils.config import load_all_configs
from .route import route_vac
from ..logging import log
from ruamel.yaml import YAML
from io import StringIO
# check it here:
# https://editor.swagger.io/

def config_to_swagger():
    """
    Load configuration files and generate a Swagger specification.

    This function loads the 'vacConfig' and 'agentConfig' configuration files,
    validates their presence, and then generates a Swagger specification
    based on these configurations.

    Returns:
        str: The generated Swagger specification in YAML format.

    Raises:
        ValueError: If 'vacConfig' or 'agentConfig' is not loaded.

    Example:
    ```python
        swagger_yaml = config_to_swagger()
        print(swagger_yaml)
    ```
    """
    configs = load_all_configs()

    vac_config = configs.get('vacConfig')
    agent_config = configs.get('agentConfig')

    if not vac_config:
        raise ValueError("Need valid 'vacConfig' loaded")
    
    if not agent_config:
        raise ValueError("Need valid 'agentConfig' loaded")
    
    swag = generate_swagger(vac_config, agent_config)

    return swag

def generate_swagger(vac_config, agent_config):
    """
    Generate a Swagger specification based on the provided configurations.

    This function creates a Swagger specification using the provided 'vacConfig'
    and 'agentConfig'. It dynamically builds paths and responses based on the
    configurations.

    Args:
        vac_config (dict): The VAC configuration.
        agent_config (dict): The agent configuration.

    Returns:
        str: The generated Swagger specification in YAML format.

    Example:
    ```python
        vac_config = {
            'vac': {
                'service1': {
                    'llm': 'vertex',
                    'model': 'gemini-1.5-flash-001',
                    'agent': 'langserve'
                },
                'service2': {
                    'llm': 'openai',
                    'agent': 'crewai',
                    'secrets': ['OPENAI_API_KEY']
                }
            }
        }
        
        agent_config = {
            'agents': {
                'default': {
                    'stream': "{stem}/vac/streaming/{vector_name}",
                    'invoke': "{stem}/vac/{vector_name}",
                    'post': {
                        'stream': "{stem}/vac/streaming/{vector_name}",
                        'invoke': "{stem}/vac/{vector_name}",
                        'openai': "{stem}/openai/v1/chat/completions",
                        'openai-vac': "{stem}/openai/v1/chat/completions/{vector_name}"
                    },
                    'get': {
                        'home': "{stem}/",
                        'health': "{stem}/health"
                    },
                    'response': {
                        'invoke': {
                            '200': {
                                'description': 'Successful invocation response',
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'answer': {'type': 'string'},
                                        'source_documents': {
                                            'type': 'array',
                                            'items': {
                                                'type': 'object',
                                                'properties': {
                                                    'page_content': {'type': 'string'},
                                                    'metadata': {'type': 'string'}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        swagger_yaml = generate_swagger(vac_config, agent_config)
        print(swagger_yaml)
        ```
    """
    swagger_template = {
        'swagger': '2.0',
        'info': {
            'title': 'Multivac - Cloud Endpoints + Cloud Run',
            'description': 'Multivac - Cloud Endpoints with a Cloud Run backend',
            'version': '0.1.0'
        },
        'host': '${_ENDPOINTS_HOST}',
        'schemes': ['https'],
        'produces': ['application/json'],
        'paths': {},
        'securityDefinitions': { 
            'ApiKeyAuth': {        # For private VAC endpoint
                'type': 'apiKey',
                'name': 'x-api-key', # Custom header name for API key
                'in': 'header'
            },
            'None': {              # For public documentation
                'type': 'apiKey',
                'name': 'allow',    # Dummy parameter for public access
                'in': 'query'       # Use query parameter to avoid interfering with other headers
            }
        }
    }
    
    vac_services = vac_config['vac']
    
    for vector_name, config in vac_services.items():
        agent_type = config['agent']
        agent_config_paths = agent_config['agents'].get(agent_type, {})
        log.info(f'Configuring swagger for agent_type: {agent_type} for vector_name: {vector_name}')
        try:
            stem = route_vac(vector_name).strip()
        except ValueError:
            stem = f"${{{agent_type.upper()}_BACKEND_URL}}"
            log.warning(f"Failed to find URL stem for {vector_name}/{agent_type} - using {stem} instead")
        
        for method, endpoints in agent_config_paths.items():
            if method not in ['get', 'post']:
                log.warning(f"Skipping {endpoints}")
                continue
            for endpoint_key, endpoint_template in endpoints.items():
                endpoint_template = endpoint_template.strip()
                endpoint_address = endpoint_template.replace("{stem}", stem).replace("{vector_name}", vector_name).strip()
                endpoint_path = endpoint_template.replace("{stem}", f"/{agent_type}").replace("{vector_name}", vector_name).strip()
                log.debug(f"Endpoint_template: {endpoint_template}")
                log.debug(f"endpoint address: {endpoint_address}")
                log.debug(f"endpoint_path: {endpoint_path}")
                if endpoint_path not in swagger_template['paths']:
                    swagger_template['paths'][endpoint_path] = {}

                operation_id = f"{method}_{agent_type}_{endpoint_key}_{vector_name}"

                swagger_template['paths'][endpoint_path][method] = {
                    'summary': f"{method.capitalize()} {vector_name}",
                    'operationId': operation_id,
                    'x-google-backend': {
                        'address': endpoint_address,
                        'protocol': 'h2'
                    },
                    'security': [{'ApiKeyAuth': []}] if method == 'post' else [{'None': []}],
                    'responses': copy.deepcopy(agent_config_paths.get('response', {}).get(endpoint_key, {
                        '200': {
                            'description': 'Default - A successful response',
                            'schema': {
                                'type': 'string'
                            }
                        }
                    }))
                }
    # Handle default agent configuration for agent types without specific entries
    default_agent_config = agent_config['agents'].get('default', {})
    
    for vector_name, config in vac_services.items():
        agent_type = config['agent']
        if agent_type in agent_config['agents']:
            continue
        log.info(f'Applying default configuration for agent_type: {agent_type} for vector_name: {vector_name}')
        try:
            stem = route_vac(vector_name).strip()
        except ValueError:
            stem = f"${{{agent_type.upper()}_BACKEND_URL}}"
            log.warning(f"Failed to find URL stem for {vector_name}/{agent_type} - using {stem} instead")
        
        for method, endpoints in default_agent_config.items():
            if method not in ['get', 'post']:
                continue
            for endpoint_key, endpoint_template in endpoints.items():
                endpoint_template = endpoint_template.strip()
                endpoint_address = endpoint_template.replace("{stem}", stem).replace("{vector_name}", vector_name).strip()
                endpoint_path = endpoint_template.replace("{stem}", f"/{agent_type}").replace("{vector_name}", vector_name).strip()
                log.debug(f"default Endpoint_template: {endpoint_template}")
                log.debug(f"default endpoint address: {endpoint_address}")
                log.debug(f"default endpoint_path: {endpoint_path}")
                if endpoint_path not in swagger_template['paths']:
                    swagger_template['paths'][endpoint_path] = {}
                
                operation_id = f"{method}_{agent_type}_{endpoint_key}_{vector_name}"

                swagger_template['paths'][endpoint_path][method] = {
                    'summary': f"{method.capitalize()} {agent_type}",
                    'operationId': operation_id,
                    'x-google-backend': {
                        'address': endpoint_address,
                        'protocol': 'h2'
                    },
                    'security': [{'ApiKeyAuth': []}] if method == 'post' else [{'None': []}],
                    'responses': copy.deepcopy(default_agent_config.get('response', {}).get(endpoint_key, {
                        '200': {
                            'description': 'Default - A successful response',
                            'schema': {
                                'type': 'string'
                            }
                        }
                    }))
                }

    yaml = YAML()
    yaml.width = 4096 # to avoid breaking urls

    # Capture YAML output in a string buffer
    string_stream = StringIO()
    yaml.dump(swagger_template, string_stream)
    yaml_string = string_stream.getvalue()

    return yaml_string
    