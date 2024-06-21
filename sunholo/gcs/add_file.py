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
import base64
import uuid

try:
    from google.cloud import storage
except ImportError:
    storage = None

from ..logging import log
from ..utils.config import load_config_key


def handle_base64_image(base64_data, vector_name):
    try:
        header, encoded = base64_data.split(",", 1)
        data = base64.b64decode(encoded)

        filename = f"{uuid.uuid4()}.jpg"
        with open(filename, "wb") as f:
            f.write(data)

        image_uri = add_file_to_gcs(filename, vector_name)
        os.remove(filename)  # Clean up the saved file
        return image_uri, "image/jpeg"
    except Exception as e:
        raise Exception(f'Base64 image upload failed: {str(e)}')

def add_file_to_gcs(filename: str, vector_name:str, bucket_name: str=None, metadata:dict=None, bucket_filepath:str=None):

    if not storage:
        return None
    
    try:
        storage_client = storage.Client()
    except Exception as err:
        log.error(f"Error creating storage client: {str(err)}")
        return None
    
    if bucket_name is None:
        bucket_config = load_config_key("upload", vector_name, "vacConfig")
        if bucket_config:
            if bucket_config.get("buckets"):
                bucket_name = bucket_config.get("buckets").get("all")

    bucket_name = bucket_name if bucket_name else os.getenv('GCS_BUCKET', None)
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

    if not bucket_filepath:
        bucket_filepath = f"{vector_name}/{year}/{month}/{day}/{hour}/{os.path.basename(filename)}"
    bucket_filepath_prev = f"{vector_name}/{year}/{month}/{day}/{hour_prev}/{os.path.basename(filename)}"

    blob = bucket.blob(bucket_filepath)
    blob_prev = bucket.blob(bucket_filepath_prev)

    if blob.exists():
        log.info(f"File {filename} already exists in gs://{bucket_name}/{bucket_filepath}")
        return f"gs://{bucket_name}/{bucket_filepath}"

    if blob_prev.exists():
        log.info(f"File {filename} already exists in gs://{bucket_name}/{bucket_filepath_prev}")
        return f"gs://{bucket_name}/{bucket_filepath_prev}"

    log.debug(f"File {filename} does not already exist in bucket {bucket_name}/{bucket_filepath}")

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
            log.info(f"File {filename} uploaded to gs://{bucket_name}/{bucket_filepath}")
            break  # Success! Exit the loop.
        except Exception as e:
            # In case of an exception (timeout, etc.), wait and then retry
            log.warning(f"Upload attempt {attempt + 1} failed with error: {str(e)}. Retrying...")
            time.sleep(base_delay * (2 ** attempt))  # Exponential backoff

    else:  # This block executes if the loop completes without breaking
        log.error(f"Failed to upload file {filename} to gs://{bucket_name}/{bucket_filepath} after {max_retries} attempts.")

    return f"gs://{bucket_name}/{bucket_filepath}"

def get_pdf_split_file_name(object_id, part_name):
    # Get the base file name without the file extension and directory
    base_name = os.path.basename(object_id).rsplit('.', 1)[0]

    # Return the full object name for the image
    return f"{os.path.dirname(object_id)}/{base_name}/pdf_parts/{part_name}"

def get_summary_file_name(object_id):
    # Get the base file name without the file extension and directory
    base_name = os.path.basename(object_id).rsplit('.', 1)[0]

    # Return the full object name for the image
    return f"{os.path.dirname(object_id)}/{base_name}/summary.md"    

def get_image_file_name(object_id, image_name, mime_type):
    # Get the base file name without the file extension and directory
    base_name = os.path.basename(object_id).rsplit('.', 1)[0]
    # Define a mapping from MIME types to file extensions
    file_extension_mapping = {
        "image/jpeg": "jpeg",
        "image/png": "png",
        "image/gif": "gif",
        # Add other MIME types and extensions as needed
    }
    # Get the file extension for the given mime type
    file_extension = file_extension_mapping.get(mime_type, "jpeg")
    # Return the full object name for the image
    return f"{os.path.dirname(object_id)}/{base_name}/img/{image_name}.{file_extension}"

