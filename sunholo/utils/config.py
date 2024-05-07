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

try:
    from google.cloud import storage
except ImportError:
    storage = None

def fetch_config(bucket_name: str, blob_name: str):
    """
    Fetch the configuration file from a Google Cloud Storage bucket.

    Args:
        bucket_name (str): The name of the GCS bucket.
        blob_name (str): The name of the blob/file to fetch.

    Returns:
        datetime or None: The last modified time of the file, or None if the blob does not exist.

    Example:
    ```python
    last_updated = fetch_config('my-bucket', 'config.yaml')
    if last_updated:
        print(f'Configuration file was last updated on {last_updated}')
    else:
        print('Configuration file not found in the specified bucket.')
    ```
    """
    from ..logging import log

    if not storage:
        log.debug("No google.cloud.storage client installed. Skipping config load from bucket")
        return None
    
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = storage.Blob(blob_name, bucket)

    # Check if the file exists
    if not blob.exists():
        log.info(f"The blob {blob_name} does not exist in the bucket {bucket_name}")
        return None

    # Download the file to a local file
    blob.download_to_filename(blob_name)

    # Get the blob's updated time
    updated_time = blob.updated

    return updated_time

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

def load_config_key(key: str, vector_name: str, filename: str=None):
    """
    Load a specific key from a configuration file.

    Args:
        key (str): The key to fetch from the configuration.
        vector_name (str): The name of the vector in the configuration file.
        filename (str, optional): The configuration file name. Defaults to the `_CONFIG_FILE` environment variable.

    Returns:
        str: The value associated with the specified key.

    Example:
    ```python
    api_url = load_config_key('apiUrl', 'myVector', 'config.yaml')
    print(f'API URL: {api_url}')
    ```
    """
    from ..logging import log
    
    assert isinstance(key, str), f"key must be a string got a {type(key)}"
    assert isinstance(vector_name, str), f"vector_name must be a string, got a {type(vector_name)}"
    
    config, filename = load_config(filename)
    log.info(f"Fetching {key} for {vector_name}")
    apiVersion = config.get('apiVersion')
    kind = config.get('kind')
    vac = config.get('vac')

    if not apiVersion or not kind:
        log.warning("Deprecated config file, move to config with `apiVersion` and `kind` set")
        vac_config = config.get(vector_name)
    else:
        log.info(f"Loaded config file {kind}/{apiVersion}")
    
    if kind == 'vacConfig':
        vac = config.get('vac')
        if not vac:
            raise ValueError("Deprecated config file, move to config with `vac:` at top level for `vector_name`")
        vac_config = vac.get(vector_name)

    if not vac_config:
        raise ValueError(f"No config array was found for {vector_name} in {filename}")
    
    log.info(f'vac_config: {vac_config} for {vector_name} - fetching "{key}"')

    key_value = vac_config.get(key)
    
    return key_value