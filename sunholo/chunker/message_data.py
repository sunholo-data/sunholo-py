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
from ..custom_logging import log

import pathlib
import tempfile
import os
import re
import json

try:
    from google.cloud import storage
except ImportError:
    storage = None

try:
    from azure.storage.blob import BlobServiceClient
except ImportError:
    BlobServiceClient = None

from langchain.schema import Document


from .splitter import chunk_doc_to_docs
from .pdfs import split_pdf_to_pages
from .publish import publish_if_urls
from . import loaders

from ..utils.parsers import extract_urls
from ..gcs.add_file import add_file_to_gcs, get_pdf_split_file_name
from ..azure.blobs import extract_blob_parts
from ..azure.auth import azure_auth

def handle_gcs_message(message_data: str, metadata: dict, vector_name: str):

    if not storage:
        log.warning("No GCS storage client")
        return None, None
    # Process message from Google Cloud Storage
    log.debug("Detected gs://")
    bucket_name, file_name = message_data[5:].split("/", 1)

    # Create a client
    storage_client = storage.Client()

    # Download the file from GCS
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)

    file_name=pathlib.Path(file_name)

    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_file_path = os.path.join(temp_dir, file_name.name)
        blob.download_to_filename(tmp_file_path)

        if file_name.suffix.lower() == ".pdf":
            pages = split_pdf_to_pages(tmp_file_path, temp_dir)
            if not metadata.get("source"):
                metadata["source"] = str(file_name)
            if len(pages) > 1: # we send it back to GCS to parrallise the imports
                log.info(f"Got back {len(pages)} pages for file {tmp_file_path}")
                for pp in pages:
                    pp_basename = os.path.basename(pp)
                    # file_name/pdf_parts/file_name_1.pdf
                    bucket_path = get_pdf_split_file_name(file_name, part_name=pp_basename)
                    gs_file = add_file_to_gcs(pp, 
                                              vector_name=vector_name, 
                                              bucket_name=bucket_name, 
                                              metadata=metadata,
                                              bucket_filepath=bucket_path)
                    log.info(f"{gs_file} is now in bucket {bucket_name}")
                log.info(f"Sent split pages for {file_name.name} back to GCS to parrallise the imports")
                return None, None
        else:
            # just original temp file
            pages = [tmp_file_path]

        the_metadata = {
            "type": "file_load_gcs",
            "bucket_name": bucket_name
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

def handle_google_drive_message(message_data: str, metadata: dict, vector_name: str):
    # Process message from Google Drive
    log.info("Got google drive URL")
    urls = extract_urls(message_data)

    docs = []
    for url in urls:
        metadata["source"] = url
        metadata["url"] = url
        metadata["type"] = "url_load"
        doc = loaders.read_gdrive_to_document(url, metadata=metadata)
        if doc is None:
            log.info("Could not load any Google Drive docs")
        else:
            docs.extend(doc)

    chunks = chunk_doc_to_docs(docs, vector_name=vector_name)

    return chunks, metadata

def handle_github_message(message_data: str, metadata: dict, vector_name: str):
    # Process message from GitHub
    log.info("Got GitHub URL")
    urls = extract_urls(message_data)

    branch="main"
    if "branch:" in message_data:
        match = re.search(r'branch:(\w+)', message_data)
        if match:
            branch = match.group(1)
    
    log.info(f"Using branch: {branch}")

    docs = []
    for url in urls:
        metadata["source"] = url
        metadata["url"] = url
        metadata["type"] = "url_load"
        doc = loaders.read_git_repo(url, branch=branch, metadata=metadata)
        if doc is None:
            log.info("Could not load GitHub files")
        else:
            docs.extend(doc)
    
    chunks = chunk_doc_to_docs(docs, vector_name=vector_name)
    
    return chunks, metadata

def handle_http_message(message_data: str, metadata: dict, vector_name:str):
    # Process message from a generic HTTP URL
    log.info(f"Got http message: {message_data}")

    # just in case, extract the URL again
    urls = extract_urls(message_data)

    docs = []
    for url in urls:
        metadata["source"] = url
        metadata["url"] = url
        metadata["type"] = "url_load"
        doc = loaders.read_url_to_document(url, metadata=metadata)
        docs.extend(doc)

    chunks = chunk_doc_to_docs(docs, vector_name=vector_name)

    return chunks, metadata

def handle_json_content_message(message_data: dict, metadata: dict, vector_name: str):
    log.info("No tailored message_data detected, processing message json")
    # Process message containing direct JSON content
    try:
        the_json = json.loads(message_data)
    except Exception as e:
        log.error(f"Could not load message {message_data} as JSON - {str(e)}")
        return None, {"metadata": f"Could not load message as JSON - {str(e)}"}
    
    the_metadata = the_json.get("metadata", {})
    metadata.update(the_metadata)
    the_content = the_json.get("page_content", None)

    if metadata.get("source", None) is not None:
        metadata["source"] = "No source embedded"

    if the_content is None:
        log.info("No content found")
        return None, {"metadata": "No content found in 'page_content' JSON field"}
    
    docs = [Document(page_content=the_content, metadata=metadata)]

    publish_if_urls(the_content, vector_name)

    chunks = chunk_doc_to_docs(docs, vector_name=vector_name)

    return chunks, metadata


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
                    container_client = blob_service_client.get_container_client(container=container_name)
                    with open(file=pp, mode="rb") as page_file:
                        blob_client = container_client.upload_blob(name=azure_blob_path, data=page_file, overwrite=True)

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