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
from langchain.document_loaders.unstructured import UnstructuredFileLoader
from langchain.document_loaders.unstructured import UnstructuredAPIFileLoader
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.document_loaders.git import GitLoader
from langchain_community.document_loaders import GoogleDriveLoader

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

from ..logging import setup_logging
from .pdfs import read_pdf_file
from ..utils.config import load_config

logging = setup_logging()
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

        # Identify type of URL
        try:
            service = build("drive", "v3", credentials=self._load_credentials())
            file = service.files().get(fileId=id).execute()
        except HttpError as err:
            logging.error(f"Error loading file {url}: {str(err)}")
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
    logging.info(f"Reading git repo from {clone_url} - {branch}")
    GIT_PAT = os.getenv('GIT_PAT', None)
    if GIT_PAT is None:
        logging.warning("No GIT_PAT is specified, won't be able to clone private git repositories")
    else:
        clone_url = clone_url.replace('https://', f'https://{GIT_PAT}@')
        logging.info("Using private GIT_PAT")

    with tempfile.TemporaryDirectory() as tmp_dir:
            try:    
                loader = GitLoader(repo_path=tmp_dir, 
                                   clone_url=clone_url, 
                                   branch=branch,
                                   file_filter=ignore_files)
            except Exception as err:
                logging.error(f"Failed to load repository: {str(err)}")
                return None
            docs = loader.load()

            if not docs:
                return None
            
            if metadata is not None:
                for doc in docs:
                    doc.metadata.update(metadata)
            
    logging.info(f"GitLoader read {len(docs)} doc(s) from {clone_url}")
        
    return docs


def read_gdrive_to_document(url: str, metadata: dict = None):

    logging.info(f"Reading gdrive doc from {url}")

    loader = MyGoogleDriveLoader(url=url)
    docs = loader.load_from_url(url)
    
    if docs is None or len(docs) == 0:
        return None
    
    if metadata is not None:
        for doc in docs:
            doc.metadata.update(metadata)
    
    logging.info(f"GoogleDriveLoader read {len(docs)} doc(s) from {url}")

    return docs

def read_url_to_document(url: str, metadata: dict = None):
    
    loader = UnstructuredURLLoader(urls=[url])
    docs = loader.load()
    if metadata is not None:
        for doc in docs:
            doc.metadata.update(metadata)
    
    logging.info(f"UnstructuredURLLoader docs: {docs}")
    
    return docs

def read_file_to_document(gs_file: pathlib.Path, split=False, metadata: dict = None):
    
    docs = []
    done = False
    pdf_path = pathlib.Path(gs_file)
    if pdf_path.suffix == ".pdf":
        
        local_doc = read_pdf_file(pdf_path, metadata=metadata)
        if local_doc is not None:
            docs.append(local_doc)
            done = True
    
    if not done:
        try:
            logging.info(f"Sending {gs_file} to UnstructuredAPIFileLoader")
            UNSTRUCTURED_URL = os.getenv("UNSTRUCTURED_URL", None)
            if UNSTRUCTURED_URL is not None:
                logging.debug(f"Found UNSTRUCTURED_URL: {UNSTRUCTURED_URL}")
                the_endpoint = f"{UNSTRUCTURED_URL}/general/v0/general"
                loader = UnstructuredAPIFileLoader(gs_file, url=the_endpoint)
            else:
                loader = UnstructuredAPIFileLoader(gs_file, api_key=UNSTRUCTURED_KEY)
            
            if split:
                # only supported for some file types
                docs = loader.load_and_split()
            else:
                start = time.time()
                docs = loader.load() # this takes a long time 30m+ for big PDF files
                end = time.time()
                elapsed_time = round((end - start) / 60, 2)
                logging.info(f"Loaded docs for {gs_file} from UnstructuredAPIFileLoader took {elapsed_time} mins")
        except ValueError as e:
            logging.info(f"Error for {gs_file} from UnstructuredAPIFileLoader: {str(e)}")
            if "file type is not supported in partition" in str(e):
                logging.info("trying locally via .txt conversion")
                txt_file = None
                try:
                    # Convert the file to .txt and try again
                    txt_file = convert_to_txt(gs_file)
                    loader = UnstructuredFileLoader(txt_file, mode="elements")
                    if split:
                        docs = loader.load_and_split()
                    else:
                        docs = loader.load()

                except Exception as inner_e:
                    raise Exception("An error occurred during txt conversion or loading.") from inner_e

                finally:
                    # Ensure cleanup happens if txt_file was created
                    if txt_file is not None and os.path.exists(txt_file):
                        os.remove(txt_file)

    for doc in docs:
        #doc.metadata["file_sha1"] = file_sha1
        logging.info(f"doc_content: {doc.page_content[:30]} - length: {len(doc.page_content)}")
        if metadata is not None:
            doc.metadata.update(metadata)
    
    logging.info(f"gs_file:{gs_file} read into {len(docs)} docs")

    return docs