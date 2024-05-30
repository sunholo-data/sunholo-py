import uuid
from google.auth import default

from ..logging import log

import hashlib
import platform
import socket

def generate_user_id():
    data = f"{socket.gethostname()}-{platform.platform()}-{platform.processor()}"
    hashed_id = hashlib.sha256(data.encode('utf-8')).hexdigest()
    return hashed_id

def generate_uuid_from_gcloud_user():
    """
    Generates a UUID using the Google Cloud authorized user's email address, or if not available via os settings.

    Returns:
        str: The generated UUID as a string.
    """
    _, credentials = default()  # Get the default credentials

    if credentials:
        user_email = credentials.service_account_email  # Get email for service accounts
        if not user_email:
            user_email = credentials.id_token['email']  # Get email for user accounts

        if user_email:
            # Create a UUID using the user's email as a source for randomness
            user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_email)
            return str(user_uuid)
        else:
            log.warning("Unable to get user email from Google Cloud credentials.")
            
    else:
        log.warning("No Google Cloud credentials found.")

    return str(generate_user_id())  