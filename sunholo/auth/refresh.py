# needs to be in minimal to check gcp
import os

import google.auth 
from google.auth.transport import requests
from ..utils.gcp import is_running_on_gcp


from ..custom_logging import log

def get_default_email():
    if not refresh_credentials():
        log.error("Could not refresh the credentials properly.")
        return None
    # https://stackoverflow.com/questions/64234214/how-to-generate-a-blob-signed-url-in-google-cloud-run

    gcs_credentials, project_id = get_default_creds()

    service_account_email = getattr(gcs_credentials, 'service_account_email', None)
    # If you use a service account credential, you can use the embedded email
    if not service_account_email:
        service_account_email = os.getenv('GCS_MAIL_USER')
        if not service_account_email:
            log.error("Could not create the credentials for signed requests - no credentials.service_account_email or GCS_MAIL_USER with roles/iam.serviceAccountTokenCreator")
            
            return None
    
    log.info(f"Found default email: {service_account_email=} for {project_id=}")
    return service_account_email

def get_default_creds():
    gcs_credentials = None
    project_id = None
    gcs_credentials, project_id = google.auth.default()

    return gcs_credentials, project_id

def refresh_credentials():
    if not is_running_on_gcp():
        log.debug("Not running on Google Cloud so no credentials available for GCS.")
        return False
    
    gcs_credentials, project_id = get_default_creds()

    if not gcs_credentials.token or gcs_credentials.expired or not gcs_credentials.valid:
        try:
            gcs_credentials.refresh(requests.Request())

            return True
        
        except Exception as e:
            log.error(f"Failed to refresh gcs credentials: {e}")

            return False
    
