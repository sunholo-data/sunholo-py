from ..utils import load_config_key
from ..logging import log
from ..database.alloydb import create_alloydb_table, create_alloydb_engine
from ..components import get_llm
from ..gcs.add_file import add_file_to_gcs, get_summary_file_name

import tempfile
import uuid
from langchain.docstore.document import Document

from langchain_google_alloydb_pg import AlloyDBDocumentSaver
from langchain_core.output_parsers import StrOutputParser

def send_doc_to_docstore(docs, vector_name):

    # docs all come from the same file but got split into a list of document objects

    docstore_config = load_config_key("docstore", vector_name=vector_name, filename="config/llm_config.yaml")
    if docstore_config is None:
        log.info(f"No docstore config found for {vector_name} ")
        
        return
    
    log.info(f"Docstore config: {docstore_config}")
     
    for docstore in docstore_config:
        for key, value in docstore.items(): 
            log.info(f"Found memory {key}")
            type = value.get('type')
            if type == 'alloydb':
                # upload to alloydb
                log.info(f"Uploading to docstore alloydb the docs for {vector_name}")

                engine = create_alloydb_engine(vector_name)
                
                table_name = f"{vector_name}_docstore"

                # merge docs into one document object
                big_doc = Document(page_content="", 
                                   metadata={"images_base64": [],
                                             "chunk_metadata": []})
                for doc in docs:
                    big_doc.page_content += f"\n{doc.page_content}"
                    if doc.metadata.get("image_base64"):
                        big_doc.metadata["images_base64"].extend(doc.metadata["image_base64"])
                        doc.metadata["image_base64"] = "moved_to_parent_doc_images"

                    for key, value in doc.metadata.items():
                        if key not in big_doc.metadata:
                            big_doc.metadata[key] = value
                    
                    big_doc.metadata["chunk_metadata"].append(doc.metadata)

                big_doc.metadata["doc_id"] = uuid.uuid4()
                big_doc.metadata["char_count"] = len(big_doc.page_content)
                if len(big_doc.content) == 0 and not doc.metadata.get("images_base64"):
                    log.warning("No content found to add for big_doc {metadata.}")
                    return None
                
                saver = AlloyDBDocumentSaver.create_sync(
                    engine=engine,
                    table_name=table_name,
                    metadata_columns=["source", "doc_id", "images_base64", "chunk_metadata"]
                )
                saver.add_documents([big_doc])
                log.info(f"Saved docs to alloydb docstore: {table_name}")

            #elif docstore.get('type') == 'cloudstorage':
            else:
                log.info(f"No docstore type found for {vector_name}: {docstore}")


def summarise_docs(docs, vector_name, summary_threshold_default=10000, model_limit_default=100000):
    chunker_config = load_config_key("chunker", vector_name=vector_name, filename="config/llm_config.yaml")
    summarise_chunking_config = chunker_config.get("summarise") if chunker_config else None
    
    if not summarise_chunking_config:
        return docs

    # if model not specified will use default config.llm
    model = summarise_chunking_config.get("model")
    summary_threshold = summarise_chunking_config.get("threshold") if summarise_chunking_config.get("threshold") else summary_threshold_default
    model_limit = summarise_chunking_config.get("model_limit") if summarise_chunking_config.get("model_limit") else model_limit_default
    
    summary_llm = get_llm(vector_name, model=model)

    for doc in docs:
        try:
            if len(doc.page_content) > summary_threshold:

                context = doc.page_content[:model_limit]
                metadata = doc.metadata
                if len(doc.page_content) > model_limit:
                    log.warning(f"Page content was above model_limit for summary: [{len(doc.page_content)} / {model_limit}]: {metadata}")
                    #TODO: use map_reduce chain for summary instead

                log.info(f"Creating summary for {metadata} for doc [{len(context)}]")
                
                prompt = f"Summarise the context below.  Be careful not to add any speculation or any details that are not covered in the original:\n## Context:{context}\n## Your Summary:\n"

                summary = summary_llm | prompt | StrOutputParser()
                log.info(f"Created a summary for {metadata}: {len(context)} > {len(summary)}")
                
                # Create a temporary file for the summary
                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                    temp_file.write(summary)
                    temp_file_path = temp_file.name  # Get the temporary file's path
                    bucket_filepath=get_summary_file_name(metadata["objectId"])
                    summary_loc = add_file_to_gcs(temp_file_path, vector_name=vector_name, metadata=metadata, bucket_filepath=bucket_filepath)
                    doc.metadata["summary_file"] = summary_loc
        except Exception as err:
            log.error(f"Failed to create a summary for {metadata}: {str(err)}")
    
    
    return docs

