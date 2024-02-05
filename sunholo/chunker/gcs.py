#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import datetime
import os

from ..logging import setup_logging

logging = setup_logging()

from google.cloud import storage

def add_file_to_gcs(filename: str, vector_name:str, bucket_name: str=None, metadata:dict=None):

    storage_client = storage.Client()

    bucket_name = bucket_name if bucket_name is not None else os.getenv('GCS_BUCKET', None)
    if bucket_name is None:
        raise ValueError("No bucket found to upload to: GCS_BUCKET returned None")
    
    if bucket_name.startswith("gs://"):
        bucket_name = bucket_name.removeprefix("gs://")
    
    bucket = storage_client.get_bucket(bucket_name)
    now = datetime.datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d") 
    hour = now.strftime("%H")
    hour_prev = (now - datetime.timedelta(hours=1)).strftime("%H")

    bucket_filepath = f"{vector_name}/{year}/{month}/{day}/{hour}/{os.path.basename(filename)}"
    bucket_filepath_prev = f"{vector_name}/{year}/{month}/{day}/{hour_prev}/{os.path.basename(filename)}"

    blob = bucket.blob(bucket_filepath)
    blob_prev = bucket.blob(bucket_filepath_prev)

    if blob.exists():
        logging.info(f"File {filename} already exists in gs://{bucket_name}/{bucket_filepath}")
        return f"gs://{bucket_name}/{bucket_filepath}"

    if blob_prev.exists():
        logging.info(f"File {filename} already exists in gs://{bucket_name}/{bucket_filepath_prev}")
        return f"gs://{bucket_name}/{bucket_filepath_prev}"

    logging.debug(f"File {filename} does not already exist in bucket {bucket_name}/{bucket_filepath}")

    the_metadata = {
        "vector_name": vector_name,
    }
    if metadata is not None:
        the_metadata.update(metadata)

    blob.metadata = the_metadata
    
    import time

    max_retries = 5
    base_delay = 1  # 1 second
    for attempt in range(max_retries):
        try:
            blob.upload_from_filename(filename)
            logging.info(f"File {filename} uploaded to gs://{bucket_name}/{bucket_filepath}")
            break  # Success! Exit the loop.
        except Exception as e:
            # In case of an exception (timeout, etc.), wait and then retry
            logging.warning(f"Upload attempt {attempt + 1} failed with error: {str(e)}. Retrying...")
            time.sleep(base_delay * (2 ** attempt))  # Exponential backoff

    else:  # This block executes if the loop completes without breaking
        logging.error(f"Failed to upload file {filename} to gs://{bucket_name}/{bucket_filepath} after {max_retries} attempts.")

    return f"gs://{bucket_name}/{bucket_filepath}"