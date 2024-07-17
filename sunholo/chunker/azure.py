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
import pathlib
import tempfile
import os

from ..logging import log
from ..azure import process_azure_blob_event
from ..azure.blobs import extract_blob_parts
from ..azure.auth import azure_auth
from ..invoke import invoke_vac
from .process_chunker_data import process_chunker_data
from ..chunker.encode_metadata import create_metadata, encode_data
from ..agents.route import read_cloud_run_url
from . import loaders
from .splitter import chunk_doc_to_docs
from .pdfs import split_pdf_to_pages

try:
    from azure.storage.blob import BlobServiceClient
except ImportError:
    BlobServiceClient = None

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
            all_chunks.extend(chunks)
    
    if not all_chunks:
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


def handle_azure_blob(message_data: str, metadata: dict, vector_name: str):
    """
    Processes a message from Azure Blob storage, downloads the file, processes it,
    and returns chunks and metadata.

    Args:
        message_data (str): URL of the Azure blob.
        metadata (dict): Metadata associated with the file.
        vector_name (str): Vector name for processing.

    Returns:
        chunks (list): List of document chunks.
        metadata (dict): Updated metadata.
    """

    if BlobServiceClient is None:
        raise ImportError("BlobServiceClient is not installed - install via pip install sunholo[azure]")

    account_name, container_name, blob_name = extract_blob_parts(message_data)

    credential = azure_auth()
    if credential is None:
        log.error("BlobServiceClient could not find auth credentials")
        return None, None
    
    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=credential)

    # Get the blob client
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    file_name = pathlib.Path(blob_name)

    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_file_path = os.path.join(temp_dir, file_name.name)
        with open(tmp_file_path, "wb") as file:
            download_stream = blob_client.download_blob()
            file.write(download_stream.readall())

        if file_name.suffix.lower() == ".pdf":
            pages = split_pdf_to_pages(tmp_file_path, temp_dir)
            if not metadata.get("source"):
                metadata["source"] = str(file_name)
            if len(pages) > 1:
                log.info(f"Got back {len(pages)} pages for file {tmp_file_path}")
                for pp in pages:
                    pp_basename = os.path.basename(pp)
                    # file_name/pdf_parts/file_name_1.pdf
                    azure_blob_path = f"{file_name.stem}_parts/{pp_basename}"
                    # Upload split pages back to Azure Blob storage
                    with open(pp, "rb") as page_file:
                        blob_client.upload_blob(name=azure_blob_path, data=page_file)
                    log.info(f"{azure_blob_path} is now in container {container_name}")
                log.info(f"Sent split pages for {file_name.name} back to Azure Blob to parallelize the imports")
                return None, None
        else:
            # just original temp file
            pages = [tmp_file_path]

        the_metadata = {
            "type": "file_load_azure_blob",
            "container_name": container_name
        }

        if metadata.get("source") is None:
            the_metadata["source"] = str(file_name)

        metadata.update(the_metadata)

        docs = []
        for page in pages:
            log.info(f"Sending file {page} to loaders.read_file_to_documents {metadata}")
            docs2 = loaders.read_file_to_documents(page, metadata=metadata)
            if docs2 is None:
                log.warning(f"loaders.read_file_to_documents docs2 failed to load file {metadata}")
            docs.extend(docs2)

        if docs is None:
            log.warning(f"loaders.read_file_to_documents docs failed to load file {metadata}")
            return None, metadata
        else:
            chunks = chunk_doc_to_docs(docs, file_name.suffix, vector_name=vector_name)

        return chunks, metadata