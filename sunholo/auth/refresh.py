# needs to be in minimal to check gcp
import os

import google.auth 
from google.auth.transport import requests
from ..utils.gcp import is_running_on_gcp
from ..custom_logging import log

def get_default_email():

    # https://stackoverflow.com/questions/64234214/how-to-generate-a-blob-signed-url-in-google-cloud-run

    gcs_credentials, project_id = refresh_credentials()

    if gcs_credentials is None:
        log.error("Could not refresh the credentials properly.")
        return None

    service_account_email = getattr(gcs_credentials, 'service_account_email', None)
    # If you use a service account credential, you can use the embedded email
    if not service_account_email:
        service_account_email = os.getenv('GCS_MAIL_USER')
        if not service_account_email:
            log.error("Could not create the credentials for signed requests - no credentials.service_account_email or GCS_MAIL_USER with roles/iam.serviceAccountTokenCreator")
            
            return None
    
    log.info(f"Found default email: {service_account_email=} for {project_id=}")
    return service_account_email, gcs_credentials

def get_default_creds():
    gcs_credentials = None
    project_id = None
    gcs_credentials, project_id = google.auth.default()

    return gcs_credentials, project_id

def refresh_credentials():
    """
    Need to refresh to get a valid email/token for signing URLs from a default service account
    """
    if not is_running_on_gcp():
        log.debug("Not running on Google Cloud so no credentials available for GCS.")
        return None, None
    
    gcs_credentials, project_id = get_default_creds()

    if not gcs_credentials.token or gcs_credentials.expired or not gcs_credentials.valid:
        try:
            r = requests.Request()
            gcs_credentials.refresh(r)

            return gcs_credentials, project_id
        
        except Exception as e:
            log.error(f"Failed to refresh gcs credentials: {e}")

            return None, None
    
