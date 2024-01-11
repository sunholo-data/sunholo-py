# from https://github.com/sunholo-data/genai-databases-retrieval-app/blob/main/langchain_tools_demo/agent.py
import os
import inspect
import google.auth.transport.requests  # type: ignore
import google.oauth2.id_token  # type: ignore
from typing import Dict, Optional
from ..utils.config import load_config
from ..utils.gcp import is_running_on_cloudrun
from ..logging import setup_logging

logging = setup_logging()

def get_run_url(service_name=None):
    if os.environ.get('SERVICE_URL') is not None:
        return os.environ.get('SERVICE_URL')
    
    if service_name is None:
        service_name = os.getenv('SERVICE_NAME')
    
    if not service_name:
        raise ValueError('Service name was not specified')
    
    cloud_urls, _ = load_config('config/cloud_run_urls.json')
    try:
        logging.info(f'Looking up URL for {service_name}')
        url = cloud_urls[service_name]
        os.environ['SERVICE_URL'] = url
        return url
    except KeyError:
        raise ValueError(f'Could not find cloud_run_url for {service_name} within {cloud_urls}')

def get_id_token(url: str) -> str:
    """Helper method to generate ID tokens for authenticated requests"""
    # Use Application Default Credentials on Cloud Run
    if is_running_on_cloudrun():
        auth_req = google.auth.transport.requests.Request()
        logging.info(f'Got id_token for {url}')
        return google.oauth2.id_token.fetch_id_token(auth_req, url)
    else:
        # Use gcloud credentials locally
        import subprocess

        return (
            subprocess.run(
                ["gcloud", "auth", "print-identity-token"],
                stdout=subprocess.PIPE,
                check=True,
            )
            .stdout.strip()
            .decode()
        )

def get_header() -> Optional[dict]:
    if is_running_on_cloudrun():
        run_url = get_run_url()
    else:
        run_url = "127.0.0.1:8080"

    if "http://" in run_url:
        return None
    else:
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
        logging.info(deets)
        headers = {"Authorization": f"Bearer {get_id_token(run_url)}"}
        return headers