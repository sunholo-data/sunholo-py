# from https://github.com/sunholo-data/genai-databases-retrieval-app/blob/main/langchain_tools_demo/agent.py
import os
import inspect
import google.auth.transport.requests  # type: ignore
import google.oauth2.id_token  # type: ignore
from typing import Dict, Optional
from ..utils.config import load_config_key, load_config
from ..utils.gcp import is_running_on_cloudrun
from ..logging import setup_logging
from ..agents.route import route_qna

logging = setup_logging()

def get_run_url(vector_name=None):

    if not vector_name:
        raise ValueError('Vector name was not specified')
    
    cloud_urls, _ = load_config('config/cloud_run_urls.json')
    agent = load_config_key("agent", vector_name=vector_name, filename="config/llm_config.yaml")

    try:
        logging.info(f'Looking up URL for {agent}')
        url = cloud_urls[agent]
        return url
    except KeyError:
        raise ValueError(f'Could not find cloud_run_url for {agent} within {cloud_urls}')

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

def get_header(vector_name) -> Optional[dict]:
    if is_running_on_cloudrun():
        run_url = get_run_url(vector_name)
    else:
        run_url = "http://127.0.0.1:8080"

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
        logging.info(f"Authenticating for run_url {run_url} from {caller_frame.f_code.co_name}")
        id_token = get_id_token(run_url)
        headers = {"Authorization": f"Bearer {id_token}"}
        #logging.info(f"id_token {id_token}")
        return headers