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
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_community.document_loaders import UnstructuredAPIFileLoader
from langchain_community.document_loaders import UnstructuredURLLoader

from langchain_community.document_loaders import GitLoader
from langchain_community.document_loaders import GoogleDriveLoader

from ..custom_logging import log
from .pdfs import read_pdf_file
from ..utils.config import load_config

import pathlib
import os
import shutil
from urllib.parse import urlparse, unquote
import tempfile
import time

from pydantic import BaseModel, Field
from typing import Optional

UNSTRUCTURED_KEY=os.getenv('UNSTRUCTURED_KEY')

# utility functions
def convert_to_txt(file_path):
    file_dir, file_name = os.path.split(file_path)
    file_base, file_ext = os.path.splitext(file_name)
    txt_file = os.path.join(file_dir, f"{file_base}.txt")
    shutil.copyfile(file_path, txt_file)
    return txt_file


class MyGoogleDriveLoader(GoogleDriveLoader):
    url: Optional[str] = Field(None)

    def __init__(self, url, *args, **kwargs):
        super().__init__(*args, **kwargs, file_ids=['dummy']) # Pass dummy value
        self.url = url

    def _extract_id(self, url):
        parsed_url = urlparse(unquote(url))
        path_parts = parsed_url.path.split('/')
        
        # Iterate over the parts
        for part in path_parts:
            # IDs are typically alphanumeric and at least a few characters long
            # So let's say that to be an ID, a part has to be at least 15 characters long
            if all(char.isalnum() or char in ['_', '-'] for char in part) and len(part) >= 15:
                return part
        
        # Return None if no ID was found
        return None

    def load_from_url(self, url: str):
        id = self._extract_id(url)
        from googleapiclient.errors import HttpError
        from googleapiclient.discovery import build

        # Identify type of URL
        try:
            service = build("drive", "v3", credentials=self._load_credentials())
            file = service.files().get(fileId=id).execute()
        except HttpError as err:
            log.error(f"Error loading file {url}: {str(err)}")
            raise

        mime_type = file["mimeType"]

        if "folder" in mime_type:
            # If it's a folder, load documents from the folder
            return self._load_documents_from_folder(id)
        else:
            # If it's not a folder, treat it as a single file
            if mime_type == "application/vnd.google-apps.document":
                return [self._load_document_from_id(id)]
            elif mime_type == "application/vnd.google-apps.spreadsheet":
                return self._load_sheet_from_id(id)
            elif mime_type == "application/pdf":
                return [self._load_file_from_id(id)]
            else:
                return []

def ignore_files(filepath):
    """Returns True if the given path's file extension is found within 
    config.json "code_extensions" array
    Returns False if not
    """
    # Load the configuration
    config = load_config("config/loader_config.yaml")

    code_extensions = config.get("extensions", [])

    lower_filepath = filepath.lower()
    # TRUE if on the list, FALSE if not
    return any(lower_filepath.endswith(ext) for ext in code_extensions)

def read_git_repo(clone_url, branch="main", metadata=None):
    log.info(f"Reading git repo from {clone_url} - {branch}")
    GIT_PAT = os.getenv('GIT_PAT', None)
    if GIT_PAT is None:
        log.warning("No GIT_PAT is specified, won't be able to clone private git repositories")
    else:
        clone_url = clone_url.replace('https://', f'https://{GIT_PAT}@')
        log.info("Using private GIT_PAT")

    with tempfile.TemporaryDirectory() as tmp_dir:
            try:    
                loader = GitLoader(repo_path=tmp_dir, 
                                   clone_url=clone_url, 
                                   branch=branch,
                                   file_filter=ignore_files)
            except Exception as err:
                log.error(f"Failed to load repository: {str(err)}")
                return None
            docs = loader.load()

            if not docs:
                return None
            
            if metadata is not None:
                for doc in docs:
                    doc.metadata.update(metadata)
            
    log.info(f"GitLoader read {len(docs)} doc(s) from {clone_url}")
        
    return docs


def read_gdrive_to_document(url: str, metadata: dict = None):

    log.info(f"Reading gdrive doc from {url}")

    loader = MyGoogleDriveLoader(url=url)
    docs = loader.load_from_url(url)
    
    if docs is None or len(docs) == 0:
        return None
    
    if metadata is not None:
        for doc in docs:
            doc.metadata.update(metadata)
    
    log.info(f"GoogleDriveLoader read {len(docs)} doc(s) from {url}")

    return docs

def read_url_to_document(url: str, metadata: dict = None):

    unstructured_kwargs = {"pdf_infer_table_structure": True,
                            "extract_image_block_types":  ["Image", "Table"]
                            }
    loader = UnstructuredURLLoader(urls=[url], mode="elements", unstructured_kwargs=unstructured_kwargs)
    docs = loader.load()
    if metadata is not None:
        for doc in docs:
            doc.metadata.update(metadata)
            if not doc.metadata.get("source") and doc.metadata.get("url"):
                doc.metadata["source"] = doc.metadata["url"]
    
    log.info(f"UnstructuredURLLoader docs: {docs}")
    
    return docs

def read_file_to_documents(gs_file: pathlib.Path, metadata: dict = None):
    
    docs = []
    pdf_path = str(pathlib.Path(gs_file))

    if metadata:
        if metadata.get("uploaded_to_bucket"):
            log.info(f"Already uploaded to bucket, skipping {pdf_path}")
            return []

    log.info(f"Sending {pdf_path} to UnstructuredAPIFileLoader")
    UNSTRUCTURED_URL = os.getenv("UNSTRUCTURED_URL")
    unstructured_kwargs = {"pdf_infer_table_structure": True,
                            "extract_image_block_types":  ["Image", "Table"]
                            }
    
    if UNSTRUCTURED_URL:
        log.debug(f"Found UNSTRUCTURED_URL: {UNSTRUCTURED_URL}")
        the_endpoint = f"{UNSTRUCTURED_URL}/general/v0/general"
        try:
            loader = UnstructuredAPIFileLoader(
                pdf_path,
                url=the_endpoint,
                mode="elements",
                **unstructured_kwargs)
        except Exception as err:
            if "'utf-8' codec can't decode byte" in str(err):
                log.error(f"Unstructured can't decode byte for {gs_file}: {str(err)} - aborting")
                return []
            else:
                raise err
    else:
        loader = UnstructuredAPIFileLoader(
            pdf_path,
            api_key=UNSTRUCTURED_KEY,
            mode="elements",
            **unstructured_kwargs)
    
    start = time.time()
    try:
        docs = loader.load() # this takes a long time 30m+ for big PDF files
    except ValueError as e:
        log.info(f"Error for {gs_file} from UnstructuredAPIFileLoader: {str(e)}")
        pdf_path = pathlib.Path(gs_file)
        if pdf_path.suffix == ".pdf":
            local_doc = read_pdf_file(pdf_path, metadata=metadata)
            if local_doc is not None:
                docs.append(local_doc)

        elif "file type is not supported in partition" in str(e):
            txt_docs = convert_to_txt_and_extract(gs_file, split=False)
            if txt_docs:
                docs.extend(txt_docs)
            else:
                log.warning("Could not extract any docs for {gs_file}")
    
    end = time.time()
    elapsed_time = round((end - start) / 60, 2)
    log.info(f"Loaded docs for {gs_file} from read_file_to_docs took {elapsed_time} mins")

    if not isinstance(docs, list):
        log.warning(f"read_file_to_documents for {gs_file} returned not a list got {type(docs)})")
        docs = [docs] 

    total_doc_chars = 0
    doc_chunk = 0
    for doc in docs:
        log.info(f"{gs_file} doc_content: {doc.page_content[:30]} - length: {len(doc.page_content)}")
        total_doc_chars += len(doc.page_content)
        doc.metadata["doc_chunk"] = doc_chunk
        doc_chunk += 1
        if metadata is not None:
            doc.metadata.update(metadata)
            log_meta = metadata.copy()
            if 'image_base64' in log_meta:
                log_meta['image_base64'] = "XXXtruncatedXXXX"
            log.info(f"doc_metadata: {log_meta}")
    
    for doc in docs:
        doc.metadata["parse_total_doc_chars"] = total_doc_chars
        doc.metadata["parse_total_doc_chunks"] = doc_chunk
    
    log.info(f"gs_file:{gs_file} read into {len(docs)} docs. parse_total_doc_chars: {total_doc_chars} - parse_total_doc_chunks {doc_chunk}")

    return docs

def convert_to_txt_and_extract(gs_file, split=False):

    log.info("trying file parsing locally via .txt conversion")
    txt_file = None
    docs = []
    try:
        # Convert the file to .txt and try again
        txt_file = convert_to_txt(gs_file)
        loader = UnstructuredFileLoader(
            txt_file, 
            mode="elements")

        docs = loader.load_and_split() if split else loader.load()

    except Exception as inner_e:
        raise Exception("An error occurred during txt conversion or loading.") from inner_e

    finally:
        # Ensure cleanup happens if txt_file was created
        if txt_file is not None and os.path.exists(txt_file):
            os.remove(txt_file)
    
    return docs