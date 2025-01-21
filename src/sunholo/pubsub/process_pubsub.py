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
import base64
from ..custom_logging import log
from ..gcs.metadata import get_object_metadata


def decode_pubsub_message(data: dict) -> tuple:
    """Extracts message data and metadata from a Pub/Sub message.

    Args:
        data (dict): The Pub/Sub message data.

    Returns:
        tuple: A tuple containing the message data and attributes as metadata.
    """
    message_data = base64.b64decode(data['message']['data']).decode('utf-8')
    attributes = data['message'].get('attributes', {})
    messageId = data['message'].get('messageId')
    publishTime = data['message'].get('publishTime')
    vector_name = attributes.get('namespace', None)
    if vector_name:
        attributes['vector_name'] = vector_name

    log.info(f"Process Pub/Sub was triggered by messageId {messageId} published at {publishTime}")
    log.debug(f"Process Pub/Sub data: {message_data}")

    return message_data, attributes, vector_name

def process_pubsub_message(data: dict) -> tuple:
    """Extracts message data and metadata from a Pub/Sub message for a Cloud Storage event.

    Args:
        data (dict): The Pub/Sub message data.

    Returns:
        tuple: A tuple containing the message data and attributes as metadata.
    """
    # Decode the message data
    message_data, attributes, vector_name = decode_pubsub_message(data)

    # Check for a valid GCS event type and payload format
    if attributes.get("eventType") == "OBJECT_FINALIZE" and attributes.get("payloadFormat") == "JSON_API_V1":
        objectId = attributes.get("objectId")
        log.info(f"Got valid event from Google Cloud Storage: {objectId}")

        # Ignore config files
        if objectId.startswith("config"):
            log.info("Ignoring config file")
            return None, None, None

        # Construct the message_data
        message_data = 'gs://' + attributes.get("bucketId") + '/' + objectId
        
        if '/' in objectId:
            bucket_vector_name = objectId.split('/')[0]
            if len(bucket_vector_name) > 0 and vector_name != bucket_vector_name:
                log.info(f"Overwriting vector_name {vector_name} with {bucket_vector_name}")
                vector_name = bucket_vector_name
        
        # get metadata for object
        metadata = get_object_metadata(attributes.get("bucketId"), attributes.get("objectId"))
        if metadata:
            metadata.update(attributes)
            attributes = metadata

    return message_data, attributes, vector_name