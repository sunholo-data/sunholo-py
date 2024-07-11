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

from ..logging import log
from ..azure import process_azure_blob_event
from .process_chunker_data import process_chunker_data

def data_to_embed_azure(events: list):
    """Triggered from a message on an Azure Data Grid event.
    Args:
         data JSON
    """
    validation_event_type = "Microsoft.EventGrid.SubscriptionValidationEvent"
    storage_blob_created_event = "Microsoft.Storage.BlobCreated"
    
    for event in events:
        event_type = event['eventType']
        data = event['data']

        if event_type == validation_event_type:
            validation_code = data['validationCode']
            log.info(f"Got SubscriptionValidation event data, validation code: {validation_code}, topic: {event['topic']}")
            
            # Return the validation response
            return {"ValidationResponse": validation_code}
        elif event_type == storage_blob_created_event:

            message_data, metadata, vector_name = process_azure_blob_event(events)

            return process_chunker_data(message_data, metadata, vector_name)
