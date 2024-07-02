from ..logging import log
from ..utils.gcp_project import get_gcp_project
import os

def init_genai():
    """
    There are some features that come to the google.generativeai first, 
    which needs to be authenticated via a GOOGLE_API_KEY environment variable, 
    created via the Google AI Console at https://aistudio.google.com/app/apikey 
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("google.generativeai not installed, please install via 'pip install sunholo[gcp]")
    
    GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError("google.generativeai needs GOOGLE_API_KEY set in environment variable")

    genai.configure(api_key=GOOGLE_API_KEY)

def init_vertex(gcp_config=None, location="eu"):
    """
    Initializes the Vertex AI environment using the provided Google Cloud Platform configuration.

    This function configures the Vertex AI API session with specified project and location details
    from the gcp_config dictionary. It is essential to call this function at the beginning of a session
    before performing any operations related to Vertex AI.

    Parameters:
        gcp_config (dict): A dictionary containing the Google Cloud Platform configuration with keys:
            - 'project_id': The Google Cloud project ID to configure for Vertex AI.
            - 'location': The Google Cloud region to configure for Vertex AI.
            If default None it will derive it from the environment

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
    
    if gcp_config:
        # Initialize Vertex AI API once per session
        project_id = gcp_config.get('project_id')
        location = gcp_config.get('location') or location
    else:
        project_id = get_gcp_project()

    vertexai.init(project=project_id, location=location)
