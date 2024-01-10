# from https://github.com/sunholo-data/genai-databases-retrieval-app/blob/main/langchain_tools_demo/agent.py
import os, sys
import google.auth.transport.requests  # type: ignore
import google.oauth2.id_token  # type: ignore
from typing import Dict, Optional
from ..utils.config import load_config

def get_run_url(service_name=None):
    if os.environ.get('SERVICE_URL') is not None:
        return os.environ.get('SERVICE_URL')
    
    if service_name is None:
        service_name = sys.getenv('SERVICE_NAME')
    cloud_urls, _ = load_config('cloud_run_urls.json')
    try:
        url = cloud_urls[service_name]
        os.environ['SERVICE_URL'] = url
        return url
    except KeyError:
        raise ValueError('Could not find cloud_run_url for {service_name} within {cloud_urls}')

def get_id_token(url: str) -> str:
    """Helper method to generate ID tokens for authenticated requests"""
    # Use Application Default Credentials on Cloud Run
    if os.getenv("K_SERVICE"):
        auth_req = google.auth.transport.requests.Request()
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
    run_url = get_run_url()
    if "http://" in run_url:
        return None
    else:
        # Append ID Token to make authenticated requests to Cloud Run services
        headers = {"Authorization": f"Bearer {get_id_token(run_url)}"}
        return headers