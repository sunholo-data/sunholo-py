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
from .vectorstore import pick_vectorstore
from ..utils import load_config_key
from .llm import get_embeddings
from ..utils.gcp_project import get_gcp_project

from langchain.retrievers import MergerRetriever
from langchain_community.retrievers import GoogleCloudEnterpriseSearchRetriever
# https://python.langchain.com/docs/integrations/retrievers/merger_retriever
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain.retrievers import ContextualCompressionRetriever



def load_memories(vector_name):
    memories = load_config_key("memory", vector_name, kind="vacConfig")
    log.info(f"Found memory settings for {vector_name}: {memories}")
    if not memories or len(memories) == 0:
        log.info(f"No memory settings found for {vector_name}")
        return None

    return memories

def pick_retriever(vector_name, embeddings=None):

    memories = load_memories(vector_name)

    retriever_list = []
    for memory in memories:  # Iterate over the list
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore:
                log.info(f"Found vectorstore {vectorstore}")
                from_metadata_id = value.get('from_metadata_id')
                if from_metadata_id:
                    # this entry needs to be fetched via metadata key
                    log.info(f"Skipped from_metadata_id for {vectorstore}")
                    continue

                embeddings = embeddings or get_embeddings(vector_name)
                read_only = value.get('read_only')
                try:
                    vectorstore = pick_vectorstore(vectorstore, 
                                                vector_name=vector_name, 
                                                embeddings=embeddings, 
                                                read_only=read_only)
                except Exception as e:
                    log.error(f"Failed to pick_vectorstore {vectorstore} for {vector_name} - {str(e)} - skipping")
                    continue
                
                k_override = value.get('k', 3)
                if vectorstore:
                    vs_retriever = vectorstore.as_retriever(search_kwargs=dict(k=k_override))
                    retriever_list.append(vs_retriever)
                else:
                    log.warning(f"No vectorstore found despite being in config: {key=}")
            
            if value.get('provider') == "GoogleCloudEnterpriseSearchRetriever":
                log.info(f"Found GoogleCloudEnterpriseSearchRetriever {value['provider']}")
                gcp_retriever = GoogleCloudEnterpriseSearchRetriever(
                    project_id=get_gcp_project(),
                    search_engine_id=value["db_id"],
                    location_id=value.get("location", "global"),
                    engine_data_type=1 if value.get("type","unstructured") == "structured" else 0,
                    query_expansion_condition=2
                )
                retriever_list.append(gcp_retriever)
            
            #TODO: more memory stores here

    if not retriever_list or len(retriever_list) == 0:
        log.info(f"No retrievers were created for {memories}")
        return None
    
    retriever = process_retrieval(retriever_list, vector_name)

    return retriever

def metadata_retriever(metadata: dict, key: str, vector_name:str, embeddings=None):
    """
    Decides which vector_name to retrieve from metadata passed
    """
    memories = load_memories(vector_name)

    retriever_list = []
    for memory in memories:  # Iterate over the list
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore:
                log.info(f"Found vectorstore {vectorstore}")
                from_metadata_id = value.get('from_metadata_id')
                if from_metadata_id:
                    # this entry needs to be fetched via metadata key
                    log.info(f"Finding id from_metadata_id for {vectorstore}")
                    if key not in metadata:
                        raise ValueError(f"Missing {key} in {metadata}")
                    the_id = metadata[key]
                    read_only = value.get('read_only')
                    embeddings = embeddings or get_embeddings(vector_name)
                    vectorstore = pick_vectorstore(vectorstore, 
                                                   vector_name=the_id, 
                                                   embeddings=embeddings, 
                                                   read_only=read_only)
                    k_override = value.get('k', 3)
                    id_retriever = vectorstore.as_retriever(search_kwargs=dict(k=k_override))
                    retriever_list.append(id_retriever)
                else:
                    continue

    if not retriever_list or len(retriever_list) == 0:
        log.info(f"No retrievers were created for {memories}")
        return None
    
    retriever = process_retrieval(retriever_list, vector_name)

    return retriever
    


def process_retrieval(retriever_list: list, vector_name: str):
    k_override = load_config_key("memory_k", vector_name, kind="vacConfig")
    lotr = MergerRetriever(retrievers=retriever_list)

    filter_embeddings = get_embeddings(vector_name)
    filter = EmbeddingsRedundantFilter(embeddings=filter_embeddings)
    pipeline = DocumentCompressorPipeline(transformers=[filter])
    retriever = ContextualCompressionRetriever(
        base_compressor=pipeline, base_retriever=lotr, 
        k=k_override)
    
    return retriever