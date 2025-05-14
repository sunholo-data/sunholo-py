try:
    from google.cloud import storage
except ImportError:
    storage = None

from ..custom_logging import log


def get_object_metadata(bucket_name, object_name):

    if not storage:
        return None

    if bucket_name is None or object_name is None:
        log.warning("Got invalid bucket name and object name")
        return None
    try:
        storage_client = storage.Client()
    except Exception as e:
        log.warning(f"Could not connect to Google Cloud Storage for metadata: {str(e)}")
        return None

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    # Fetch the blob's metadata
    blob.reload()  # Make sure to reload the blob to get the most up-to-date metadata

    # Access custom metadata
    custom_metadata = blob.metadata

    log.info(f"Custom Metadata for {object_name}: {custom_metadata}")
    return custom_metadata

def check_gcs_file_size(source: str) -> int:
    """
    Check the size of a file in Google Cloud Storage without downloading the entire file.
    
    Args:
        source: str The Google Cloud Storage URI of the file to check (e.g., 'gs://bucket_name/file_name').
        
    Returns:
        int: The size of the file in bytes, or -1 if the size cannot be determined.
    """
    from google.cloud import storage
    
    try:
        # Parse the GCS URI
        if not source.startswith('gs://'):
            log.warning(f"Invalid GCS URI format: {source}")
            return -1
            
        bucket_name, blob_path = source[5:].split('/', 1)
        
        # Create a client and get the bucket
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Get the blob (file) and retrieve its metadata
        blob = bucket.blob(blob_path)
        blob.reload()  # Fetch the latest metadata
        
        return blob.size
    except Exception as err:
        log.error(f"Error checking file size for {source}: {str(err)}")
        return -1