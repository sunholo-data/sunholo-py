import uuid
import base64
import json
from datetime import datetime, timezone

from ..custom_logging import log

def create_metadata(vac, metadata):
    now_utc = datetime.now(timezone.utc)
    formatted_time = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Default metadata if none provided
    default_metadata = {"vector_name": vac, "source": "sunholo-cli", "eventTime": formatted_time}

    try:
        # Merge default metadata with provided metadata
        if metadata:
            if not isinstance(metadata, dict):
                metadata = json.loads(metadata)
        else:
            metadata = {}    
    except Exception as err:
        log.error(f"[bold red]ERROR: metadata not parsed: {err} for {metadata}")

    # Update metadata with default values if not present
    metadata.update(default_metadata)

    return metadata

def encode_data(vac, content, metadata=None, local_chunks=False):

    metadata = create_metadata(vac, metadata)

    # Encode the content (URL)
    if isinstance(content, str):
        message_data = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    else:
        raise ValueError(f"Unsupported content type: {type(content)}")

    now_utc = datetime.now(timezone.utc)
    formatted_time = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Construct the message dictionary
    messageId = str(uuid.uuid4())
    message = {
        "message": {
            "data": message_data,
            "messageId": messageId,
            "publishTime": formatted_time,
            "attributes": {
                "namespace": vac,
                "return_chunks": str(local_chunks).lower()
            },
        }
    }

    # Merge metadata with attributes
    message["message"]["attributes"].update(metadata)

    #console.print()
    #console.print(f"Sending message: {messageId} with metadata:")
    #console.print(f"{message['message']['attributes']}")

    return message