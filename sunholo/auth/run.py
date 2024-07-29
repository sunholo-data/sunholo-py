# from https://github.com/sunholo-data/genai-databases-retrieval-app/blob/main/langchain_tools_demo/agent.py
import inspect

from typing import Dict, Optional
from ..utils.config import load_config
from ..utils import ConfigManager
from ..utils.gcp import is_running_on_cloudrun
from ..utils.api_key import has_multivac_api_key, get_multivac_api_key
from ..custom_logging import log
from ..agents.route import route_vac
from .gcloud import get_local_gcloud_token

def get_run_url(config):

    if not config:
        raise ValueError('Vector name was not specified')
    
    cloud_urls = route_vac(config=config)
    
    cloud_urls, _ = load_config('config/cloud_run_urls.json')
    agent = config.vacConfig("agent")

    try:
        log.info(f'Looking up URL for {agent}')
        url = cloud_urls[agent]
        return url
    except KeyError:
        raise ValueError(f'Could not find cloud_run_url for {agent} within {cloud_urls}')

def get_id_token(url: str) -> str:
    """Helper method to generate ID tokens for authenticated requests"""
    # Use Application Default Credentials on Cloud Run
    if is_running_on_cloudrun():
        import google.auth.transport.requests  # type: ignore
        import google.oauth2.id_token  # type: ignore
        auth_req = google.auth.transport.requests.Request()
        log.info(f'Got id_token for {url}')

        return google.oauth2.id_token.fetch_id_token(auth_req, url)

    return get_local_gcloud_token()

def get_cloud_run_token(vector_name):
    if has_multivac_api_key():
        
        return {"x-api-key": get_multivac_api_key()}

    #if is_running_on_cloudrun():
    #    run_url = get_run_url(vector_name)
    #else:
    #    run_url = "http://127.0.0.1:8080"
    
    config = ConfigManager(vector_name)
    run_url = get_run_url(config)

    # Append ID Token to make authenticated requests to Cloud Run services
    frame = inspect.currentframe()
    caller_frame = frame.f_back if frame is not None else None  # One level up in the stack
    deets = {
        'message': 'Authenticating for run_url',
        'run_url': run_url
    }
    if caller_frame:
        deets = {
                'message': 'Authenticating for run_url',
                'file': caller_frame.f_code.co_filename,
                'line': str(caller_frame.f_lineno),  
                'function': caller_frame.f_code.co_name,
                'run_url': run_url
            }
    log.info(f"Authenticating for run_url {run_url} from {caller_frame.f_code.co_name}")
    id_token = get_id_token(run_url)
    #log.info(f"id_token {id_token}")
    return id_token

def get_header(vector_name) -> Optional[dict]:
    id_token = get_cloud_run_token(vector_name)

    headers = {"Authorization": f"Bearer {id_token}"}
    
    return headers