import os

try:
    from google.cloud import storage 
except ImportError:
    storage = None

from ..custom_logging import log

def download_files_from_gcs(bucket_name: str, source_folder: str, destination_folder: str=None):
    """
    Download all files from a specified folder in a Google Cloud Storage bucket to a local directory.
    
    Parameters:
    - bucket_name: The name of the GCS bucket.
    - source_folder: The folder (prefix) in the GCS bucket to download files from.
    - destination_folder: The local directory to save the downloaded files, or os.getcwd() if None
    """
    try:
        storage_client = storage.Client()
    except Exception as err:
        log.error(f"Error creating storage client: {str(err)}")
        return None

    # Get the bucket
    bucket = storage_client.bucket(bucket_name)

    # List blobs in the specified folder
    blobs = bucket.list_blobs(prefix=source_folder)

    if not destination_folder:
        destination_folder = os.getcwd()

    # Ensure the destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    for blob in blobs:
        # Skip if the blob is a directory
        if blob.name.endswith('/'):
            continue
        
        # Define the local path
        local_path = os.path.join(destination_folder, os.path.relpath(blob.name, source_folder))
        
        # Ensure the local folder exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Download the blob to a local file
        blob.download_to_filename(local_path)
        log.info(f"Downloaded {blob.name} to {local_path}")