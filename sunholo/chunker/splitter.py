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
from ..utils.parsers import remove_whitespace
from langchain.schema import Document
import langchain.text_splitter as text_splitter
from .images import upload_doc_images
from .doc_handling import send_doc_to_docstore, summarise_docs
from ..database.uuid import generate_uuid_from_object_id


def chunk_doc_to_docs(documents: list, extension: str = ".md", min_size: int = 800, vector_name=None, **kwargs):
    """Turns a Document object into a list of many Document chunks.
       If a document or chunk is smaller than min_size, it will be merged with adjacent documents or chunks."""

    if len(documents)==0:
        log.warning("No documents found to chunk in chunk_doc_to_docs")
        return None

    # send full parsed doc to docstore
    docstore_doc_id, documents = send_doc_to_docstore(documents, vector_name=vector_name)

    doc_summaries = summarise_docs(documents, vector_name=vector_name)
    if doc_summaries:
        for doc in documents:
            # Assuming each doc has a unique identifier in its metadata under 'objectId'
            objectId = doc.metadata.get("objectId")
            if objectId and objectId in doc_summaries:
                # If the objectId is found in doc_summaries, add the summary location to the document's metadata
                doc.metadata["summary_location"] = doc_summaries[objectId]

    # Combine entire documents that are smaller than min_size
    combined_documents_content = ""
    combined_documents = []
    for document in documents:
        content = remove_whitespace(document.page_content)

        if docstore_doc_id:
            document.metadata["docstore_doc_id"] = docstore_doc_id
        
        if document.metadata.get("objectId") or document.metadata.get("url"):
            the_id = document.metadata.get("objectId") or document.metadata.get("url")
            document.metadata["doc_id"] = generate_uuid_from_object_id(the_id)
        else:
            log.warning(f"Could not create a doc_id for document: {document.metadata}")

        # look for images and upload them for later extraction, add metadata of location
        image_gsurl = upload_doc_images(document.metadata)
        if image_gsurl:
            document.metadata["image_gsurl"] = image_gsurl

        if len(content) < min_size:
            combined_documents_content += content + "\n"
            log.debug(f"Appending document as its smaller than {min_size}: length {len(content)} - appended doc length {len(combined_documents_content)}")
        else:
            if combined_documents_content:
                combined_documents.append(Document(page_content=combined_documents_content, metadata=document.metadata))
                combined_documents_content = ""
            combined_documents.append(document)

    if combined_documents_content:
        combined_documents.append(Document(page_content=combined_documents_content, metadata=documents[-1].metadata))

    source_chunks = []
    temporary_chunk = ""
    chunk_number = 0
    for document in combined_documents:
        splitter = choose_splitter(extension, vector_name=vector_name, **kwargs)
        for chunk in splitter.split_text(document.page_content):
            # If a chunk is smaller than the min_size, append it to temporary_chunk with a line break and continue
            if len(chunk) < min_size:
                temporary_chunk += chunk + "\n"
                log.debug(f"Appending chunk as its smaller than {min_size}: length {len(chunk)}")
                continue

            # If there's content in temporary_chunk, append it to the current chunk
            if temporary_chunk:
                chunk = temporary_chunk + chunk
                temporary_chunk = ""

            # If the combined chunk is still less than the min_size, append to temporary_chunk with a line break and continue
            if len(chunk) < min_size:
                temporary_chunk += chunk + "\n"
                log.debug(f"Appending chunk as its smaller than {min_size}: length {len(chunk)}")
                continue
            
            log.info(f"Adding chunk of length {len(chunk)}")
            document.metadata["chunk_number"] = chunk_number
            source_chunks.append(Document(page_content=chunk, metadata=document.metadata))

        # If there's any remaining content in temporary_chunk, append it as a new chunk
        if temporary_chunk:
            source_chunks.append(Document(page_content=temporary_chunk, metadata=document.metadata))
            temporary_chunk = ""
        
        chunk_number += 1

    log.info(f"Chunked into {chunk_number} documents")
    return source_chunks

def choose_splitter(extension: str, chunk_size: int=1024, chunk_overlap:int=200, vector_name: str=None):

    if vector_name:
        # check if there is a chunking configuration
        from ..utils import load_config_key
        chunk_config = load_config_key("chunker", vector_name=vector_name, kind="vacConfig")
        if chunk_config:
            if chunk_config.get("type") == "semantic":
                embedding_str = chunk_config.get("llm")
                if not embedding_str:
                    log.error("Unable to find embedding 'config.chunker.llm' configuration needed for semantic chunking")
                else:
                    log.info(f"Semantic chunking for {vector_name}")
                    from langchain_experimental.text_splitter import SemanticChunker
                    from ..components import pick_embedding
                    embeddings = pick_embedding(embedding_str)
                    semantic_splitter = SemanticChunker(
                        embeddings, breakpoint_threshold_type="percentile"
                    )

                    return semantic_splitter


    if extension == ".py":
        return text_splitter.PythonCodeTextSplitter()
    elif extension == ".md":
        return text_splitter.MarkdownTextSplitter()
    elif extension == ".html":
        return text_splitter.HTMLHeaderTextSplitter()
    
    return text_splitter.RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
