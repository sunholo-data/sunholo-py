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
import time

try:
    from google.cloud import storage
except ImportError:
    storage = None

from ..custom_logging import log
from ..utils import ConfigManager


def handle_base64_image(base64_data: str, vector_name: str, extension: str):
    """
    Handle base64 image data, decode it, save it as a file, upload it to GCS, and return the image URI and MIME type.

    Args:
        base64_data (str): The base64 encoded image data.
        vector_name (str): The vector name for the GCS path.
        extension (str): The file extension of the image (e.g., ".jpg", ".png").

    Returns:
        Tuple[str, str]: The URI of the uploaded image and the MIME type.
    """
    
    model = ConfigManager(vector_name).vacConfig("llm")
    if model.startswith("openai"):  # pass it to gpt directly
        return base64_data, base64_data.split(",", 1)

    try:
        header, encoded = base64_data.split(",", 1)
        data = base64.b64decode(encoded)

        filename = f"{str(uuid.uuid4())}{extension}"
        with open(filename, "wb") as f:
            f.write(data)

        image_uri = add_file_to_gcs(filename, vector_name)
        os.remove(filename)  # Clean up the saved file

        # Determine MIME type based on extension
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff"
        }.get(extension.lower(), "application/octet-stream")  # Default MIME type if unknown

        return image_uri, mime_type
    except Exception as e:
        raise Exception(f'Base64 image upload failed: {str(e)}')


def resolve_bucket(vector_name):
    bucket_name = None

    if os.getenv('EXTENSIONS_BUCKET'):
        log.warning('Resolving to EXTENSIONS_BUCKET environment variable')
        return os.getenv('EXTENSIONS_BUCKET')
    
    if vector_name:
        bucket_config = ConfigManager(vector_name).vacConfig("upload")

        if bucket_config:
            if bucket_config.get("buckets"):
                bucket_name = bucket_config.get("buckets").get("all")

    bucket_name = bucket_name or os.getenv('GCS_BUCKET')
    if not bucket_name:
        raise ValueError("No bucket found to upload to: GCS_BUCKET returned None")
    
    if bucket_name.startswith("gs://"):
        bucket_name = bucket_name.removeprefix("gs://")
    
    return bucket_name

def add_folder_to_gcs(
        source_folder:str, 
        vector_name:str=None, 
        bucket_name:str=None, 
        metadata:dict=None, 
        bucket_folderpath:str=None):
    """Uploads a folder and all its contents to a specified GCS bucket."""

    uris = []
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            local_path = os.path.join(root, file)
            # Create the relative path in the destination folder
            relative_path = os.path.relpath(local_path, source_folder)
            bucket_filepath = os.path.join(bucket_folderpath, relative_path)

            uri = add_file_to_gcs(local_path, 
                            vector_name=vector_name, 
                            bucket_name=bucket_name, 
                            metadata=metadata, 
                            bucket_filepath=bucket_filepath)
            uris.append(uri)
            
    log.info(f"uploaded [{len(files)}] to GCS bucket")

    return uris

def add_file_to_gcs(filename: str, 
                    vector_name:str=None, 
                    bucket_name: str=None, 
                    metadata:dict=None, 
                    bucket_filepath:str=None):

    if not storage:
        return None
    
    try:
        storage_client = storage.Client()
    except Exception as err:
        log.error(f"Error creating storage client: {str(err)}")
        return None
    
    if not bucket_name:
        bucket_name = resolve_bucket(vector_name)
    
    bucket = storage_client.get_bucket(bucket_name)
    now = datetime.datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d") 
    hour = now.strftime("%H")
    hour_prev = (now - datetime.timedelta(hours=1)).strftime("%H")

    if os.getenv('EXTENSIONS_BUCKET'):
        log.warning(f"setting {bucket_filepath=} to {os.path.basename(filename)} basename due to EXTENSIONS_BUCKET setting")
        bucket_filepath = os.path.basename(filename)

    if not vector_name:
        vector_name = "global"
    
    if not bucket_filepath:
        
        bucket_filepath = f"{vector_name}/{year}/{month}/{day}/{hour}/{os.path.basename(filename)}"
    
    bucket_filepath_prev = f"{vector_name}/{year}/{month}/{day}/{hour_prev}/{os.path.basename(filename)}"

    blob = bucket.blob(bucket_filepath)
    blob_prev = bucket.blob(bucket_filepath_prev)

    if blob.exists() and not os.getenv('EXTENSIONS_BUCKET'):
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

