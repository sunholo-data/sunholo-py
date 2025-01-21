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