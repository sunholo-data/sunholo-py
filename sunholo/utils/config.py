#   Copyright [2023] [Sunholo ApS]
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
import logging
import os
import json
import yaml
from google.cloud import storage

def fetch_config(bucket_name, blob_name):
    #global last_mod_time

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = storage.Blob(blob_name, bucket)

    # Check if the file exists
    if not blob.exists():
        logging.info(f"The blob {blob_name} does not exist in the bucket {bucket_name}")
        return None

    # Download the file to a local file
    blob.download_to_filename(blob_name)

    # Get the blob's updated time
    updated_time = blob.updated

    return updated_time

def load_config(filename=None):

    if filename is None:
        filename = os.getenv("_CONFIG_FILE", None)
        if filename is None:
            raise ValueError("No _CONFIG_FILE env value specified")

    # Join the script directory with the filename
    config_path = filename

    logging.info(f"Loading config file {os.getcwd()}/{config_path}")

    with open(config_path, 'r') as f:
        if filename.endswith(".json"):
            config = json.load(f)
        elif filename.endswith(".yaml") or filename.endswith(".yml"):
            config = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path}. The supported formats are JSON and YAML.")
    
    return config, filename

def load_config_key(key, vector_name, filename=None):
    config, filename = load_config(filename)
        
    llm_config = config.get(vector_name, None)
    if llm_config is None:
        raise ValueError(f"No config array was found for {vector_name} in {filename}")
    
    logging.info(f'llm_config: {llm_config} for {vector_name} - fetching "{key}"')

    key_value = llm_config.get(key, None)
    
    return key_value