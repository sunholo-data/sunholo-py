from ..utils import load_config_key, ConfigManager
from ..custom_logging import log
from ..database.alloydb import add_document_if_not_exists
from ..database.uuid import generate_uuid_from_object_id
from ..components.llm import llm_str_to_llm
from ..gcs.add_file import add_file_to_gcs, get_summary_file_name
from ..utils.parsers import remove_whitespace
from .images import upload_doc_images
from ..langfuse.callback import create_langfuse_callback

import tempfile
import traceback
import json
import os
from langchain.docstore.document import Document

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def send_doc_to_docstore(docs, vector_name):

    # docs all come from the same file but got split into a list of document objects

    docstore_config = load_config_key("docstore", vector_name=vector_name, kind="vacConfig")
    if docstore_config is None:
        log.info(f"No docstore config found for {vector_name} ")
        
        return None, docs
    
    log.info(f"Docstore config: {docstore_config}")

    doc_id, big_doc, docs = create_big_doc(docs)

    for docstore in docstore_config:
        for key, value in docstore.items(): 
            log.info(f"Found memory {key}")
            type = value.get('type')
            if type == 'alloydb':
                # upload to alloydb
                log.info(f"Uploading to docstore alloydb the docs for {vector_name}")

                saved_doc_id = add_document_if_not_exists(big_doc, vector_name=vector_name)
                if saved_doc_id is not None:
                    if saved_doc_id != doc_id:
                        raise ValueError(f"Something went wrong with doc_ids: {doc_id} vs saved_doc_id: {saved_doc_id}")

            #elif docstore.get('type') == 'cloudstorage':
            else:
                log.info(f"No docstore type found for {vector_name}: {docstore}")
    
    log.info(f"Added doc to docstores: {doc_id}")
    return doc_id, docs

def create_big_doc(docs):

    if not docs:
        return None, None, None
    
    # merge docs into one document object
    big_doc = Document(page_content="", 
                        metadata={"images_gsurls": [],
                                  "chunk_metadata": []})
    doc_id = None
    for doc in docs:
        if doc_id is None:
            first_source = doc.metadata.get("objectId") or doc.metadata.get("url")
            if first_source:
                doc_id = generate_uuid_from_object_id(first_source)
        
        if doc_id is None:
            raise ValueError(f"Failed to create a doc_id from {doc.metadata}")

        doc.metadata["docstore_doc_id"] = str(doc_id)

        content = remove_whitespace(doc.page_content)
        big_doc.page_content += f"\n{content}"
        
        image_gsurl = upload_doc_images(doc.metadata)
        if image_gsurl:
            doc.metadata["image_gsurl"] = image_gsurl
            doc.metadata["image_base64"] = None
            doc.metadata["uploaded_to_bucket"] = True
            big_doc.metadata["images_gsurls"].append(image_gsurl)

        for key, value in doc.metadata.items():
            if key not in big_doc.metadata:
                big_doc.metadata[key] = value
        
        big_doc.metadata["chunk_metadata"].append(doc.metadata)

    big_doc.metadata["doc_id"] = doc_id
    big_doc.metadata["char_count"] = len(big_doc.page_content)

    if len(big_doc.page_content) == 0 and not big_doc.metadata.get("images_gsurls"):
        log.warning("No content found to add for big_doc")
        return None, None, docs
    
    # Serialize lists in metadata to JSON strings before saving
    for key in ["images_gsurls", "chunk_metadata"]:
        big_doc.metadata[key] = json.dumps(big_doc.metadata[key])

    source = big_doc.metadata.get("source") or doc.metadata.get("url")
    if not source:
        log.warning(f"No source found for big_doc {doc_id} {big_doc.metadata}")
    
    return doc_id, big_doc, docs

def summarise_docs(docs, vector_name, summary_threshold_default=10000, model_limit_default=25000):

    if not docs:
        return None
    
    config = ConfigManager(vector_name)

    chunker_config = config.vacConfig("chunker")
    summarise_chunking_config = chunker_config.get("summarise") if chunker_config else None
    
    if not summarise_chunking_config:
        return None

    # if model not specified will use default config.llm
    model = summarise_chunking_config.get("model")
    summary_llm_str   = summarise_chunking_config.get("llm") if summarise_chunking_config.get("llm") else chunker_config.get("llm")
    summary_threshold = summarise_chunking_config.get("threshold") if summarise_chunking_config.get("threshold") else summary_threshold_default
    model_limit = summarise_chunking_config.get("model_limit") if summarise_chunking_config.get("model_limit") else model_limit_default

    summary_llm = llm_str_to_llm(summary_llm_str, model=model, config=config)

    doc_summaries = {}
    for doc in docs:
        try:
            if len(doc.page_content) > summary_threshold:

                context = doc.page_content[:model_limit]
                metadata = doc.metadata
                if len(doc.page_content) > model_limit:
                    log.warning(f"Page content was above model_limit for summary: [{len(doc.page_content)} / {model_limit}]: {metadata}")
                    #TODO: use map_reduce chain for summary instead

                log.info(f"Creating summary for {metadata} for doc [{len(context)}]")
                
                prompt_template = """
Summarise the context below.  
Include in the summary the title showing which document it comes from, and ensure you include any companies, people or entites involved within the text. 
Finish the summary with a list of relevant keywords that will help the summary be found via search engines. 
Be careful not to add any speculation or any details that are not covered in the original:
## Context:
{context}
## Metadata
{metadata}
## Your Summary:
"""                
                prompt = PromptTemplate.from_template(prompt_template)
                summary_chain = prompt | summary_llm | StrOutputParser()
                doc_source = doc.metadata.get('source')
                doc_objectId = doc.metadata.get('objectId')
                doc_eventTime = doc.metadata.get('eventTime')

                full_context = f"# {doc_source}\n\n## {doc_objectId}\n{doc_eventTime}\n\n## Text\n{context}"

                str_metadata = json.dumps(metadata)

                cb_langfuse = create_langfuse_callback()

                summary = summary_chain.invoke(
                        {"context": full_context, "metadata": str_metadata[:2000]},
                        config={"callbacks": [cb_langfuse]}
                    )
                
                log.info(f"Created a summary for {metadata}: {len(context)} > {len(summary)}")
                
                if len(summary) < 100:
                    log.info(f"Summary not long enough {metadata}, skipping")
                    continue

                # Create a temporary file for the summary
                bucket_name = os.getenv("DOC_BUCKET")
                if not bucket_name:
                    raise ValueError("No DOC_BUCKET configured for summary")
                
                if bucket_name.startswith("gs://"):
                    bucket_name = bucket_name[len("gs://"):]

                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                    temp_file.write(summary)
                    temp_file.flush()
                    temp_file_path = temp_file.name

                    log.info(f"Wrote summary to file {temp_file_path}: {summary[30:]}")

                    file_size = os.path.getsize(temp_file_path)
                    if file_size > 0:
                        bucket_filepath = get_summary_file_name(metadata["objectId"])
                        summary_loc = add_file_to_gcs(temp_file_path, 
                                                    vector_name=vector_name, 
                                                    bucket_name=bucket_name, 
                                                    metadata=metadata, 
                                                    bucket_filepath=bucket_filepath)
                        
                        doc_summaries[metadata["objectId"]] = summary_loc
                    else:
                        log.error(f"Summary file {temp_file_path} is empty. Skipping upload.")
        except Exception as err:
            log.error(f"Failed to create a summary for {metadata}: {str(err)} traceback: {traceback.format_exc()}")
    
    
    return doc_summaries

