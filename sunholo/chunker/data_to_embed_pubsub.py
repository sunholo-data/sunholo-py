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
from ..logging import setup_logging
from ..pubsub import process_pubsub_message
from .message_data import handle_gcs_message, handle_google_drive_message, handle_github_message, handle_http_message, handle_json_content_message
from .publish import process_docs_chunks_vector_name

logging = setup_logging()

def data_to_embed_pubsub(data: dict):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         data JSON
    """

    message_data, metadata, vector_name = process_pubsub_message(data)

    metadata["vector_name"] = vector_name

    if message_data is None:
        logging.error("No message_data was found in data: {data}")
        return

    logging.debug(f"Found metadata in pubsub: {metadata}")

    chunks = []

    if message_data.startswith("gs://"):
        chunks, metadata =  handle_gcs_message(message_data, metadata, vector_name)

    elif message_data.startswith("https://drive.google.com") or message_data.startswith("https://docs.google.com"):
        chunks, metadata = handle_google_drive_message(message_data, metadata)

    #TODO: support more git service URLs
    elif message_data.startswith("https://github.com"):
        chunks, metadata = handle_github_message(message_data, metadata)
        
    elif message_data.startswith("http"):
        chunks, metadata = handle_http_message(message_data, metadata)

    else: 
        chunks, metadata = handle_json_content_message(message_data, metadata, vector_name) 

    process_docs_chunks_vector_name(chunks, vector_name, metadata)

    # to be really sure
    metadata["vector_name"] = vector_name

    return metadata


