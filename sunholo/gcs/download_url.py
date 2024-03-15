import os
from urllib.parse import quote
from datetime import datetime, timedelta
from google.cloud import storage 
import google.auth
from google.auth.transport import requests

from ..logging import setup_logging

log = setup_logging()

def sign_gcs_url(bucket_name:str, object_name:str, expiry_secs = 86400):
    # https://stackoverflow.com/questions/64234214/how-to-generate-a-blob-signed-url-in-google-cloud-run

    credentials, project_id = google.auth.default()

    # Perform a refresh request to get the access token of the current credentials (Else, it's None)
    r = requests.Request()
    credentials.refresh(r)

    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(object_name)
    if not blob:
        return None

    expires = datetime.now() + timedelta(seconds=expiry_secs)

    # If you use a service account credential, you can use the embedded email
    if hasattr(credentials, "service_account_email"):
        service_account_email = credentials.service_account_email
    else:
        service_account_email = os.getenv('GCS_MAIL_USER')
        if service_account_email is None:
            log.error("For local testing must set a GCS_MAIL_USER to sign GCS URLs")
        log.error("Could not create the credentials for signed requests - no credentials.service_account_email or GCS_MAIL_USER with roles/iam.serviceAccountTokenCreator")
        return None

    url = blob.generate_signed_url(
        version="v4",
        expiration=expires,
        service_account_email=service_account_email, 
        access_token=credentials.token)
    log.info(f"Generated signed URL: {url}")
    return url


def construct_download_link(source_uri: str) -> str:
    """Creates a viewable Cloud Storage web browser link from a gs:// URI.""" 
    if not source_uri.startswith("gs://"):
        return source_uri  # Return the URI as is if it doesn't start with gs://

    bucket_name, object_name = parse_gs_uri(source_uri)

    signed_url = sign_gcs_url(bucket_name, object_name)
    if signed_url:
        return signed_url, os.path.basename(object_name), True
    
    log.info(f"Failed to generate signed URL for {source_uri}")
    return construct_download_link_simple(bucket_name, object_name)


def construct_download_link_simple(bucket_name:str, object_name:str) -> str:
    """Creates a viewable Cloud Storage web browser link from a gs:// URI.

    Args:
        source_uri: The gs:// URI of the object in Cloud Storage.

    Returns:
        A URL that directly access the object in the Cloud Storage web browser.
    """

    public_url = f"https://storage.cloud.google.com/{bucket_name}/{quote(object_name)}"
    filename = os.path.basename(object_name)
    signed = False
    return public_url, filename, signed

def parse_gs_uri(gs_uri: str) -> tuple[str, str]:
    """Parses a gs:// URI into the bucket name and object name.

    Args:
        gs_uri: The gs:// URI to parse.

    Returns:
        A tuple containing the bucket name and object name.
    """
    parts = gs_uri.split("/")
    if len(parts) < 3:
        raise ValueError(f"Invalid gs:// URI: {gs_uri}")
    return parts[2], "/".join(parts[3:])