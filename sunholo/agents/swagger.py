import yaml

from ..utils.config import load_all_configs, load_config_key
from .route import route_vac
from ..logging import log

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

    if not vac_config:
        raise ValueError("Need valid 'vacConfig' loaded")
    
    swag = generate_swagger(vac_config)

    return swag

def generate_swagger(vac_config):
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
        'paths': {}
    }
    
    vac_services = vac_config['vac']
    
    for service, config in vac_services.items():
        agent_type = config['agent']
        agent_config_paths = load_config_key(service, "dummy", kind="agentConfig")
        log.info(f'Configuring swagger for agent_type: {agent_type} for service: {service}')
        try:
            stem = route_vac(service)
        except ValueError:
            stem = f"${{{agent_type.upper()}_BACKEND_URL}}"
            log.warning(f"Failed to find URL stem for {service}/{agent_type} - using {stem} instead")
        
        path = f"/{service}"
        swagger_template['paths'][path] = {
            'get': {
                'summary': f"Get {service}",
                'operationId': f"get_{service}",
                'x-google-backend': {
                    'address': stem,
                    'protocol': 'h2'
                },
                'responses': agent_config_paths.get('response', {}).get('get', {
                    '200': {
                        'description': 'Default - A successful response',
                        'schema': {
                            'type': 'string'
                        }
                    }
                })
            },
            'post': {
                'summary': f"Post {service}",
                'operationId': f"post_{service}",
                'x-google-backend': {
                    'address': stem,
                    'protocol': 'h2'
                },
                'responses': agent_config_paths.get('response', {}).get('post', {
                    '200': {
                        'description': 'Default - Successful response',
                        'schema': {
                            'type': 'string'
                        }
                    }
                })
            }
        }
    
    return yaml.dump(swagger_template, default_flow_style=False)
