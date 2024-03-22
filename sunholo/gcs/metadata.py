from google.cloud import storage
from ..logging import setup_logging

logging = setup_logging()

def get_object_metadata(bucket_name, object_name):

    if bucket_name is None or object_name is None:
        logging.warning("Got invalid bucket name and object name")
        return None
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    # Fetch the blob's metadata
    blob.reload()  # Make sure to reload the blob to get the most up-to-date metadata

    # Access custom metadata
    custom_metadata = blob.metadata

    logging.info(f"Custom Metadata for {object_name}: {custom_metadata}")
    return custom_metadata