import re
from ..custom_logging import log


def is_azure_blob(message_data):
    """
    Checks if the provided URL is an Azure Blob Storage URL.

    Args:
        message_data (str): The URL to be checked.

    Returns:
        bool: True if the URL is an Azure Blob Storage URL, False otherwise.
    """
    blob_url_pattern = r"https://(.*).blob.core.windows.net/(.*)/(.*)"
    match = re.match(blob_url_pattern, message_data)
    if not match:
        return False
    
    return True

def extract_blob_parts(message_data):
    """
    Extracts the account name, container name, and blob name from an Azure Blob Storage URL.

    Args:
        message_data (str): The Azure Blob Storage URL.

    Returns:
        tuple: A tuple containing the account name, container name, and blob name.
               Returns (None, None, None) if the URL is invalid.
    """
    if not is_azure_blob(message_data):
        return None, None, None
    
    log.debug("Detected Azure blob storage URL")
    # Extract the account name, container name, and blob name from the URL
    blob_url_pattern = r"https://(.*).blob.core.windows.net/(.*)/(.*)"
    match = re.match(blob_url_pattern, message_data)
    if not match:
        log.error("Invalid Azure blob URL format")
        return None, None

    account_name, container_name, blob_name = match.groups()

    return account_name, container_name, blob_name

