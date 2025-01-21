import pathlib

from .message_data import (
    handle_gcs_message, 
    handle_google_drive_message, 
    handle_github_message, 
    handle_http_message, 
    handle_json_content_message,
    handle_azure_blob
)

from . import loaders
from ..llamaindex.import_files import llamaindex_chunker_check
from ..discovery_engine.chunker_handler import discovery_engine_chunker_check
from .publish import process_docs_chunks_vector_name
from .splitter import chunk_doc_to_docs
from ..azure.blobs import is_azure_blob
from ..utils import ConfigManager

from ..custom_logging import log

def process_chunker_data(message_data, metadata, vector_name):

    if metadata:
        metadata["vector_name"] = vector_name

    if message_data is None:
        log.warning(f"No message_data was found in data: {metadata=}")
        return

    log.debug(f"Found metadata in pubsub: {metadata=}")

    config=ConfigManager(vector_name)

    # checks if only a llamaindex chunking/embedder, return early as no other processing needed
    llamacheck = llamaindex_chunker_check(message_data, metadata, vector_name)
    if llamacheck:
        return llamacheck
    
    # if only a discovery engine memory, return early as no other processing needed
    discovery_check = discovery_engine_chunker_check(message_data, metadata, config=config)
    if discovery_check:
        return discovery_check

    chunks = []

    if message_data.startswith("gs://"):
        chunks, metadata =  handle_gcs_message(message_data, metadata, vector_name)

    elif is_azure_blob(message_data):
        chunks, metadata = handle_azure_blob(message_data, metadata, vector_name)

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

    # returns None when not on GCP
    process_docs_chunks_vector_name(chunks, vector_name, metadata)

    return metadata


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
