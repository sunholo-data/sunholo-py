import os
from urllib.parse import quote
from datetime import datetime, timedelta

# needs to be in minimal to check gcp
import google.auth 
from google.auth.transport import requests
from google.auth.exceptions import RefreshError

try:
    from google.cloud import storage 
except ImportError:
    storage = None

from ..logging import log
from ..utils.gcp import is_running_on_gcp

gcs_credentials = None
project_id = None
gcs_client = None
gcs_bucket_cache = {}

if is_running_on_gcp():
    # Perform a refresh request to get the access token of the current credentials (Else, it's None)
    gcs_credentials, project_id = google.auth.default()
    # Prepare global variables for client reuse
    if storage:
        gcs_client = storage.Client()

def refresh_credentials():
    if not is_running_on_gcp():
        log.debug("Not running on Google Cloud so no credentials available for GCS.")
        return False
    if not gcs_credentials.token or gcs_credentials.expired or not gcs_credentials.valid:
        try:
            gcs_credentials.refresh(requests.Request())
        except Exception as e:
            log.error(f"Failed to refresh gcs credentials: {e}")
            return False
    return True

refresh_credentials()

def get_bucket(bucket_name):
    if bucket_name not in gcs_bucket_cache:
        gcs_bucket_cache[bucket_name] = gcs_client.get_bucket(bucket_name)
    return gcs_bucket_cache[bucket_name]

def sign_gcs_url(bucket_name:str, object_name:str, expiry_secs = 86400):
    if not refresh_credentials():
        log.error("Could not refresh the credentials properly.")
        return None
    # https://stackoverflow.com/questions/64234214/how-to-generate-a-blob-signed-url-in-google-cloud-run

    expires = datetime.now() + timedelta(seconds=expiry_secs)

    service_account_email = getattr(gcs_credentials, 'service_account_email', None)
    # If you use a service account credential, you can use the embedded email
    if not service_account_email:
        service_account_email = os.getenv('GCS_MAIL_USER')
        if service_account_email is None:
            log.error("For local testing must set a GCS_MAIL_USER to sign GCS URLs")
        log.error("Could not create the credentials for signed requests - no credentials.service_account_email or GCS_MAIL_USER with roles/iam.serviceAccountTokenCreator")
        return None

    try:
        bucket = get_bucket(bucket_name)
        blob = bucket.blob(object_name)
        if not blob:
            return None
        url = blob.generate_signed_url(
            version="v4",
            expiration=expires,
            service_account_email=service_account_email,
            access_token=gcs_credentials.token)
        return url
    except RefreshError:
        log.info("Refreshing gcs_credentials due to token expiration.")
        refreshed = refresh_credentials()
        if refreshed:
            return sign_gcs_url(bucket_name, object_name, expiry_secs)
        log.error("Failed to refresh gcs credentials")
        return None
    except Exception as e:
        log.error(f"Failed to generate signed URL: {e}")
        return None


def construct_download_link(source_uri: str) -> tuple[str, str, bool]:
    """Creates a viewable Cloud Storage web browser link from a gs:// URI.""" 
    if not source_uri.startswith("gs://"):
        return source_uri, source_uri, False  # Return the URI as is if it doesn't start with gs://

    bucket_name, object_name = parse_gs_uri(source_uri)

    signed_url = sign_gcs_url(bucket_name, object_name)
    if signed_url:
        the_name = os.path.basename(object_name)
        log.info(f"Creating signed URL for {the_name} - {signed_url}")
        return signed_url, the_name, True
    
    log.error(f"Failed to generate signed URL for {source_uri}")
    return construct_download_link_simple(bucket_name, object_name)


def construct_download_link_simple(bucket_name:str, object_name:str) -> tuple[str, str, bool]:
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