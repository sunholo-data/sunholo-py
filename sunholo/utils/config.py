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

import os
import json
import yaml
from datetime import datetime, timedelta
from collections import defaultdict
from .timedelta import format_timedelta


def get_module_filepath(filepath: str):
    """
    Get the absolute path of a module file based on its relative path.

    Args:
        filepath (str): The relative path of the file.

    Returns:
        str: The absolute file path.

    Example:
    ```python
    abs_path = get_module_filepath('config/config.yaml')
    print(f'Absolute path: {abs_path}')
    ```
    """
    from ..logging import log
    
    # Get the root directory of this Python script
    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    # Build the full filepath by joining the directory with the filename
    filepath = os.path.join(dir_path, filepath)

    log.info(f"Found filepath {filepath}")

    return filepath

# Global cache
config_cache = {}
def load_all_configs():
    """
    Load all configuration files from the specified directory into a dictionary.
    Files are expected to be either YAML or JSON and must contain a 'kind' key at the root.
    Caching is used to avoid reloading files within a 5-minute window.
    """
    from ..logging import log

    if not os.getenv("_CONFIG_FOLDER", None):
        log.debug("_CONFIG_FOLDER is not set, using os.getcwd() instead")
    else:
        log.debug(f"_CONFIG_FOLDER set to: {os.getenv('_CONFIG_FOLDER')}")

    config_folder = os.getenv("_CONFIG_FOLDER", os.getcwd())
    config_folder = os.path.join(config_folder, "config")

    log.debug(f"Loading all configs from folder: {config_folder}")
    current_time = datetime.now()

    configs_by_kind = defaultdict(dict)
    for filename in os.listdir(config_folder):
        #log.debug(f"config file: {filename}")
        if filename in ["cloudbuild.yaml", "cloud_run_urls.json"]:
            # skip these
            continue
        if filename.endswith(('.yaml', '.yml', '.json')):
            config_file = os.path.join(config_folder, filename)
            
            # Check cache first
            if filename in config_cache:
                cached_config, cache_time = config_cache[filename]
                time_to_recache = (current_time - cache_time)
                if time_to_recache < timedelta(minutes=5):
                    config = cached_config
                else:
                    config = reload_config_file(config_file, filename)
            else:
                config = reload_config_file(config_file, filename)

            kind = config.get('kind')
            if kind:
                configs_by_kind[kind] = config
            else:
                log.warning(f"No 'kind' found in {filename}")
    
    #log.debug(f"Config recache in {format_timedelta(timedelta(minutes=5) - time_to_recache)}")

    return configs_by_kind

def reload_config_file(config_file, filename):
    """
    Helper function to load a config file and update the cache.
    """
    from ..logging import log
    with open(config_file, 'r') as file:
        if filename.endswith('.json'):
            config = json.load(file)
        else:
            config = yaml.safe_load(file)
    
    config_cache[filename] = (config, datetime.now())
    log.debug(f"Loaded and cached {config_file}")
    return config



def load_config(filename: str=None) -> tuple[dict, str]:
    """
    Load configuration from a yaml or json file.
    Will look relative to `_CONFIG_FOLDER` environment variable if available, else current directory.

    Args:
        filename (str, optional): The name of the configuration file. Defaults to the `_CONFIG_FILE` environment variable.

    Returns:
        tuple[dict, str]: The configuration as a dictionary and the derived absolute filename.

    Example:
    ```python
    config, filename = load_config('config.yaml')
    print(f'Config: {config}')
    print(f'Loaded from file: {filename}')
    ```
    """
    global config_cache
    from ..logging import log
    
    if filename is None:
        filename = os.getenv("_CONFIG_FILE", None)
        if filename is None:
            raise ValueError("No _CONFIG_FILE env value specified")

    current_time = datetime.now()

   # Check the cache first
    if filename in config_cache:
        cached_config, cache_time = config_cache[filename]
        if (current_time - cache_time) < timedelta(minutes=5):
            log.debug(f"Returning cached config for {filename}")
            return cached_config, filename
        else:
            log.debug(f"Cache expired for {filename}, reloading...")

    
    if os.getenv("_CONFIG_FOLDER"):
        log.debug(f"_CONFIG_FOLDER: {os.getenv('_CONFIG_FOLDER')}")
                  
    # Join the script directory with the filename
    config_folder = os.getenv("_CONFIG_FOLDER") if os.getenv("_CONFIG_FOLDER") else os.getcwd()

    config_file = os.path.join(config_folder, filename)
    log.debug(f"Loading config file {config_file}")

    with open(config_file, 'r') as f:
        if filename.endswith(".json"):
            config = json.load(f)
        elif filename.endswith(".yaml") or filename.endswith(".yml"):
            config = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_file}. The supported formats are JSON and YAML.")

    # Store in cache with the current time
    config_cache[filename] = (config, current_time) 
    
    return config, filename

def load_config_key(key: str, vector_name: str, kind: str):
    """
    Load a specific key from a configuration file.

    Args:
        key (str): The key to fetch from the configuration.
        vector_name (str): The name of the vector in the configuration file.
        kind: (str, optional): Specify the type of configuration to retrieve e.g. 'vacConfig' which will pick from files within `_CONFIG_FOLDER`

    Returns:
        str: The value associated with the specified key.

    Example:
    ```python
    api_url = load_config_key('apiUrl', 'myVector', kind="vacConfig")
    print(f'API URL: {api_url}')
    ```
    """
    # can't use sunholo.logging due to circular import
    from ..logging import log

    if kind != 'agentConfig':
        assert isinstance(key, str), f"key must be a string got a {type(key)}"

    assert isinstance(vector_name, str), f"vector_name must be a string, got a {type(vector_name)}"
    
    configs_by_kind = load_all_configs()

    log.debug(f"Got kind: {kind} - applying to configs")
    
    if not configs_by_kind:
        log.warning("Did not load configs via folder")
             
    config = configs_by_kind[kind]

    apiVersion = config.get('apiVersion')

    log.debug(f"Fetching '{key}' for '{vector_name}' from '{kind}/{apiVersion}'")
    
    if kind == 'vacConfig':
        if vector_name == 'global':
            key_value = config.get(key)
            log.debug(f'vac_config global value for {key}: {key_value}')

            return key_value
        
        vac = config.get('vac')
        if not vac:
            raise ValueError("Deprecated config file, move to config with `vac:` at top level for `vector_name`")
        vac_config = vac.get(vector_name)
        if not vac_config:
            log.warning(f"No config array was found for {vector_name} in {kind}")
            
            return None
        
        log.debug(f'vac_config: {vac_config} for {vector_name} - fetching "{key}"')
        key_value = vac_config.get(key)
        
        return key_value
    
    elif kind == 'promptConfig':
        prompts = config.get('prompts')
        if not prompts:
            raise ValueError("Deprecated config file, move to config with 'prompts:' at top level for `vector_name`")
        prompt_for_vector_name = prompts.get(vector_name)
        if not prompt_for_vector_name:
            raise ValueError(f"Could not find prompt for vector_name {vector_name}")
        
        log.debug(f'prompts: {prompt_for_vector_name} for {vector_name} - fetching "{key}"')
        key_value = prompt_for_vector_name.get(key)
        
        return key_value
    elif kind == 'agentConfig':
        agents = config.get('agents')

        if key in agents:
            return agents[key]
        else:
            log.info("Returning default agent endpoints")
            return agents["default"]
        
