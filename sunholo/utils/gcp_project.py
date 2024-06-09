import os
from .config import load_config_key
from .gcp import get_metadata, is_running_on_gcp
import logging

def get_env_project_id():
    """
    Attempts to retrieve the project ID from environment variables.

    Returns:
        str or None: The project ID if found in environment variables, None otherwise.
    """
    return os.environ.get('GCP_PROJECT') or os.environ.get('GOOGLE_CLOUD_PROJECT')


def get_gcp_project(include_config=False):
    """
    Retrieve the GCP project ID from environment variables or the GCP metadata server.

    Returns:
        str or None: The project ID if found, None otherwise.
    """
    if include_config: # to avoid circular imports, must be specified
        gcp_config = load_config_key("gcp_config", "global", "vacConfig")
        if gcp_config:
            if gcp_config.get('project_id'):
                return gcp_config.get('project_id')

    project_id = get_env_project_id()
    if project_id:
        return project_id
    
    project_id = get_metadata('project/project-id')
    if project_id:
        os.environ["GCP_PROJECT"] = project_id 
        return project_id

    if not is_running_on_gcp():
        return None

    logging.warning("GCP Project ID not found. Ensure you are running on GCP or have the GCP_PROJECT environment variable set.")
    return None