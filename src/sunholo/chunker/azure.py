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
import json
from datetime import datetime, timezone

from ..custom_logging import log
from ..azure import process_azure_blob_event

from ..invoke import invoke_vac
from .process_chunker_data import process_chunker_data
from ..chunker.encode_metadata import create_metadata, encode_data
from ..agents.route import read_cloud_run_url

def data_to_embed_azure(events: list):
    """Triggered from a message on an Azure Data Grid event.
    Args:
         data JSON
    """
    validation_event_type = "Microsoft.EventGrid.SubscriptionValidationEvent"
    storage_blob_created_event = "Microsoft.Storage.BlobCreated"
    
    all_chunks = []
    vac_name = None
    for event in events:
        event_type = event['eventType']
        data = event['data']

        if event_type == validation_event_type:
            validation_code = data['validationCode']
            log.info(f"Got SubscriptionValidation event data, validation code: {validation_code}, topic: {event['topic']}")
            
            # Return the validation response
            return {"ValidationResponse": validation_code}
        elif event_type == storage_blob_created_event:

            message_data, metadata, vac_name = process_azure_blob_event(events)
            metadata["return_chunks"] = True

            #TODO: process the azure blob URL and download it
            
            chunks = process_chunker_data(message_data, metadata, vac_name)
            if chunks:
                all_chunks.extend(chunks)
    
    if not all_chunks or len(chunks) == 0:
        return {'status': 'error', 'message': f'No chunks were found in events: {events}'}
    
    if not vac_name:
        return {'status': 'error', 'message': f'Could not find a valid VAC config name in payload {all_chunks}'}
    
    metadata = create_metadata(vac_name, metadata)

    embeds = []

    for chunk in chunks:
        log.info(f"Working on chunk {chunk['metadata']}")

        # do this async?
        content = chunk.get("page_content")
        now_utc = datetime.now(timezone.utc)
        formatted_time = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        chunk["metadata"]["eventTime"]  = formatted_time
        if not content:
            log.error("No content chunk found, skipping")

            continue

        log.info(f"Sending chunk length {len(content)} to embedder")
        processed_chunk = encode_data(vac = vac_name, content = json.dumps(chunk))
        
        embed_url = read_cloud_run_url('embedder')

        embed_res = invoke_vac(f"{embed_url}/embed_chunk", processed_chunk)
        embeds.append(embed_res)

    log.info("Embedding pipeline finished")
    
    return embed_res        

