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
import pathlib

from ..logging import log
from ..pubsub import process_pubsub_message
from .message_data import handle_gcs_message, handle_google_drive_message, handle_github_message, handle_http_message, handle_json_content_message
from .publish import process_docs_chunks_vector_name
from .splitter import chunk_doc_to_docs

from ..llamaindex.import_files import llamaindex_chunker_check
from ..discovery_engine.chunker_handler import discovery_engine_chunker_check

from . import loaders

def direct_file_to_embed(file_name: pathlib.Path, metadata: dict, vector_name: str):
    """
    Send direct files to chunking embed pipeline

    
    
    """
    log.info(f"Sending direct file upload {file_name} to loaders.read_file_to_documents {metadata}")
    docs = loaders.read_file_to_documents(file_name, metadata=metadata)
    if docs is None:
        log.warning(f"loaders.read_file_to_documents docs2 failed to load file {metadata}")

        return None

    chunks = chunk_doc_to_docs(docs, file_name.suffix, vector_name=vector_name)
    
    return format_chunk_return(chunks, metadata, vector_name)



def data_to_embed_pubsub(data: dict):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         data JSON
    """

    message_data, metadata, vector_name = process_pubsub_message(data)

    return process_chunker_data(message_data, metadata, vector_name)

def process_chunker_data(message_data, metadata, vector_name):

    if metadata:
        metadata["vector_name"] = vector_name

    if message_data is None:
        log.warning(f"No message_data was found in data: {metadata=}")
        return

    log.debug(f"Found metadata in pubsub: {metadata=}")

    # checks if only a llamaindex chunking/embedder, return early as no other processing needed
    llamacheck = llamaindex_chunker_check(message_data, metadata, vector_name)
    if llamacheck:
        return llamacheck
    
    # if only a discovery engine memory, return early as no other processing needed
    discovery_check = discovery_engine_chunker_check(message_data, metadata, vector_name)
    if discovery_check:
        return discovery_check

    chunks = []

    if message_data.startswith("gs://"):
        chunks, metadata =  handle_gcs_message(message_data, metadata, vector_name)

    elif message_data.startswith("https://drive.google.com") or message_data.startswith("https://docs.google.com"):
        chunks, metadata = handle_google_drive_message(message_data, metadata, vector_name)

    #TODO: support more git service URLs
    elif message_data.startswith("https://github.com"):
        chunks, metadata = handle_github_message(message_data, metadata, vector_name)
        
    elif message_data.startswith("http"):
        chunks, metadata = handle_http_message(message_data, metadata, vector_name)

    else: 
        chunks, metadata = handle_json_content_message(message_data, metadata, vector_name) 
    
    return format_chunk_return(chunks, metadata, vector_name)


def format_chunk_return(chunks, metadata, vector_name):
    # to be really sure
    if metadata:
        metadata["vector_name"] = vector_name

        if metadata.get("return_chunks"):
            log.info("attributes.return_chunks=True detected, skipping process chunks queue")
            output_list = []
            if chunks:
                for chunk in chunks:
                    output_list.append({"page_content": chunk.page_content, "metadata": chunk.metadata})
                    
            return output_list

    process_docs_chunks_vector_name(chunks, vector_name, metadata)

    return metadata


