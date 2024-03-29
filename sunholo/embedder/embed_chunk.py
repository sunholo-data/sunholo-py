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
import traceback
import base64
import json
import datetime
import yaml

from langchain.schema import Document

from ..components import get_embeddings, pick_vectorstore, load_memories, pick_embedding
from ..logging import log


def embed_pubsub_chunk(data: dict):
    """Triggered from a message on a Cloud Pub/Sub topic "embed_chunk" topic
    Will only attempt to send one chunk to vectorstore.
    Args:
         data JSON
    """

    message_data = base64.b64decode(data['message']['data']).decode('utf-8')
    messageId = data['message'].get('messageId')
    publishTime = data['message'].get('publishTime')

    log.debug(f"This Function was triggered by messageId {messageId} published at {publishTime}")

    try:
        the_json = json.loads(message_data)
    except Exception as err:
        log.error(f"Error - could not parse message_data: {err}: {message_data}")
        return "Could not parse message_data"

    if not isinstance(the_json, dict):
        raise ValueError(f"Could not parse message_data from json to a dict: got {message_data} or type: {type(the_json)}")

    page_content = the_json.get("page_content")

    metadata = the_json.get("metadata")
    if not metadata:
        raise ValueError("Could not find metadata")

    if page_content is None:
        return "No page content"
    elif len(page_content) < 100:
        log.warning(f"too little page content to add: {message_data}")
        return "Too little characters"

    vector_name = metadata.get("vector_name", None)
    if vector_name is None:
        msg = f"FATAL: No vector name was found within metadata: {metadata}"
        log.error(msg)
        return msg
    
    log.info(f"Embedding: {vector_name} page_content: {page_content[:30]}...[{len(page_content)}] - {metadata}")

    if 'eventTime' not in metadata:
        metadata['eventTime'] = datetime.datetime.now(datetime.UTC).isoformat(timespec='microseconds') + "Z"
    metadata['eventtime'] = metadata['eventTime'] # case insensitive bugs

    if 'source' not in metadata:
        if 'objectId' in metadata:
            metadata['source'] = metadata['objectId']
        else:
            log.warning(f"No source found in metadata: {metadata}")
    
    if 'original_source' not in metadata:
        metadata['original_source'] = metadata.get('source')
    else:
        metadata['source'] = metadata['original_source']
    
    if 'chunk_length' not in metadata:
        metadata['chunk_length'] = len(page_content)

    # add metadata to page_content too for vectorstores that don't support the metdata field
    chunk_metadata = f"Metadata:\n{yaml.dump(metadata)}\n"
    page_content = f"{page_content}\n{chunk_metadata}"

    doc = Document(page_content=page_content, metadata=metadata)

    # init embedding and vector store
    embeddings = get_embeddings(vector_name)

    memories = load_memories(vector_name)
    vectorstore_list = []
    for memory in memories:  # Iterate over the list
        for key, value in memory.items(): 
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore:
                # check if vectorstore specific embedding is available
                embed_llm = value.get('llm')
                if embed_llm:
                    embeddings = pick_embedding(embed_llm)
                vectorstore_obj = pick_vectorstore(vectorstore, vector_name=vector_name, embeddings=embeddings)
                vs_retriever = vectorstore_obj.as_retriever(search_kwargs=dict(k=3))
                vectorstore_list.append(vs_retriever)

    # can have multiple vectorstores per embed
    metadata_list = []
    import uuid
    for vector_store in vectorstore_list:
        log.debug(f"Adding single document for {vector_name} to vector store {vector_store}")
        try:
            vector_store.add_documents([doc], ids = [str(uuid.uuid4())])
            log.info(f"Added doc for {vector_name} to {vector_store} - metadata: {metadata}")
            metadata_list.append(metadata)
        except Exception as err:
            error_message = traceback.format_exc()
            log.error(f"Could not add document for {vector_name} to {vector_store} for {metadata}: {str(err)} traceback: {error_message}")

    return metadata_list
