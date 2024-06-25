from ..logging import log
from ..pubsub import PubSubManager
from ..utils.parsers import contains_url, extract_urls
from ..utils.gcp_project import get_gcp_project

from langchain.schema import Document

def publish_if_urls(the_content, vector_name):
    """
    Extracts URLs and puts them in a queue for processing on PubSub
    """
    if contains_url(the_content):
        log.info("Detected http://")

        urls = extract_urls(the_content)
            
        for url in urls:
            publish_text(url, vector_name)


def publish_chunks(chunks: list[Document], vector_name: str):
    project = get_gcp_project()
    if not project:
        log.warning("No GCP project found for PubSub, no message sent")

        return None
    
    log.info("Publishing chunks to embed_chunk")
    
    try:
        pubsub_manager = PubSubManager(vector_name, 
                                    pubsub_topic="chunk-to-pubsub-embed", 
                                    project_id=project)
    except Exception as err:
        log.error(f"PubSubManager init error: Could not publish chunks to {project} {vector_name} pubsub_topic chunk-to-pubsub-embed - {str(err)}")
        
        return None
        
    for chunk in chunks:
        # Convert chunk to string, as Pub/Sub messages must be strings or bytes
        chunk_str = chunk.json()
        if len(chunk_str) < 10:
            log.warning(f"Not publishing {chunk_str} as too small < 10 chars")
            continue
        log.info(f"Publishing chunk: {chunk_str}")
        pubsub_manager.publish_message(chunk_str)
    

def publish_text(text:str, vector_name: str):
    project = get_gcp_project()
    if not project:
        log.warning("No GCP project found for PubSub, no message sent")

        return None
    
    log.info(f"Publishing text: {text} to app-to-pubsub-chunk")
    pubsub_manager = PubSubManager(vector_name, 
                                   pubsub_topic="app-to-pubsub-chunk",
                                   project_id=project)
    
    pubsub_manager.publish_message(text)

def process_docs_chunks_vector_name(chunks, vector_name, metadata):
    project = get_gcp_project()
    if not project:
        log.warning("No GCP project found for PubSub, no message sent")

        return None
        
    pubsub_manager = PubSubManager(vector_name, 
                                   pubsub_topic="pubsub_state_messages",
                                   project_id=project)
    if chunks is None:
        log.info("No chunks found")
        pubsub_manager.publish_message(f"No chunks for: {metadata} to {vector_name} embedding")
        return None
        
    publish_chunks(chunks, vector_name=vector_name)

    msg = f"data_to_embed_pubsub published chunks with metadata: {metadata}"

    log.info(msg)
    
    pubsub_manager.publish_message(f"Sent doc chunks with metadata: {metadata} to {vector_name} embedding")

    return metadata   