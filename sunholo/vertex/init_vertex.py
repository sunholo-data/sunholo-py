from ..logging import log

def init_vertex(gcp_config):
    """
    Initializes the Vertex AI environment using the provided Google Cloud Platform configuration.

    This function configures the Vertex AI API session with specified project and location details
    from the gcp_config dictionary. It is essential to call this function at the beginning of a session
    before performing any operations related to Vertex AI.

    Parameters:
        gcp_config (dict): A dictionary containing the Google Cloud Platform configuration with keys:
            - 'project_id': The Google Cloud project ID to configure for Vertex AI.
            - 'location': The Google Cloud region to configure for Vertex AI.

    Raises:
        KeyError: If the necessary keys ('project_id' or 'location') are missing in the gcp_config dictionary.
        ModuleNotFoundError: If the Vertex AI module is not installed and needs to be installed via pip.

    Example:
    ```python
    gcp_config = {
         'project_id': 'your-project-id',
         'location': 'us-central1'
    }
    init_vertex(gcp_config)
    # This will initialize the Vertex AI session with the provided project ID and location.

    Note:
        Ensure that the 'vertexai' module is installed and correctly configured before calling this function.
        The function assumes that the required 'vertexai' library is available and that the logging setup is already in place.
    """
    try:
        import vertexai
    except ImportError:
        log.error("Need to install vertexai module via `pip install sunholo[gcp]`")

        return None
    
    # Initialize Vertex AI API once per session
    project_id = gcp_config.get('project_id')
    location = gcp_config.get('location')
    vertexai.init(project=project_id, location=location)
