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
from .vectorstore import pick_vectorstore
from ..utils import ConfigManager
from .llm import get_embeddings
from ..utils.gcp_project import get_gcp_project

from langchain.retrievers import MergerRetriever
from langchain_community.retrievers import GoogleCloudEnterpriseSearchRetriever
# https://python.langchain.com/docs/integrations/retrievers/merger_retriever
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain.retrievers import ContextualCompressionRetriever



def load_memories(vector_name:str=None, config:ConfigManager=None):
    if config is None:
        if vector_name is None:
            raise ValueError("vector_name and config were none")
        config = ConfigManager(vector_name)

    memories = config.vacConfig("memory")
    
    log.info(f"Found memory settings for {config.vector_name}: {memories}")
    if not memories or len(memories) == 0:
        log.info(f"No memory settings found for {vector_name}")
        return None

    return memories

def pick_retriever(vector_name:str=None, config:ConfigManager=None, embeddings=None):

    if config is None:
        if vector_name is None:
            raise ValueError("vector_name and config were none")
        config = ConfigManager(vector_name)

    memories = load_memories(config=config)

    retriever_list = []
    for memory in memories:  # Iterate over the list
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore:
                log.info(f"Found vectorstore {vectorstore}")

                if vectorstore == "vertex_ai_search" or vectorstore == "discovery_engine":
                    # use direct retriever
                    if value.get('chunks'):
                        log.warning(f"{config.vector_name} will not be using GoogleVertexAISearchRetriever with chunks vertex AI search as not supported yet")
                        continue
                    from langchain.retrievers import GoogleVertexAISearchRetriever
                    gcp_config = config.vacConfig('gcp_config')
                    try:
                        gcp_retriever = GoogleVertexAISearchRetriever(
                            data_store_id=None if value.get("search_engine_id") else config.vector_name,
                            max_documents=value.get('max_documents', 5),
                            project_id=gcp_config.get('project_id') or get_gcp_project(),
                            search_engine_id=value.get("search_engine_id"),
                            location_id=gcp_config.get("location", "global"),
                            engine_data_type=value.get("engine_data_type",0)
                        )
                    except Exception as err:
                        log.error(f"Could not init GoogleVertexAISearchRetriever - {str(err)}")
                        continue
                    
                    retriever_list.append(gcp_retriever)
                    continue

                from_metadata_id = value.get('from_metadata_id')
                if from_metadata_id:
                    # this entry needs to be fetched via metadata key
                    log.info(f"Skipped from_metadata_id for {vectorstore}")
                    continue

                embeddings = embeddings or get_embeddings(config=config)
                read_only = value.get('read_only')
                try:
                    vectorstore_obj = pick_vectorstore(
                        vectorstore, 
                        config=config,
                        embeddings=embeddings, 
                        read_only=read_only)
                except Exception as e:
                    log.error(f"Failed to pick_vectorstore {vectorstore} for {config.vector_name} - {str(e)} - skipping")
                    continue
                
                k_override = value.get('k', 3)
                if vectorstore_obj:
                    vs_retriever = vectorstore_obj.as_retriever(search_kwargs=dict(k=k_override))
                    retriever_list.append(vs_retriever)
                else:
                    log.warning(f"No vectorstore found despite being in config: {key=}")
            
            #TODO: more memory stores here

    if not retriever_list or len(retriever_list) == 0:
        log.info(f"No retrievers were created for {memories}")
        return None
    
    retriever = process_retrieval(retriever_list, config=config)

    return retriever

def metadata_retriever(metadata: dict, key: str, config:ConfigManager, embeddings=None):
    """
    Decides which vector_name to retrieve from metadata passed
    """
    memories = load_memories(config=config)

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
                    embeddings = embeddings or get_embeddings(config=config)
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
    
    retriever = process_retrieval(retriever_list, config=config)

    return retriever
    


def process_retrieval(retriever_list: list, config: ConfigManager):
    k_override = config.vacConfig('memory_k')
    lotr = MergerRetriever(retrievers=retriever_list)

    filter_embeddings = get_embeddings(config=config)

    filter = EmbeddingsRedundantFilter(embeddings=filter_embeddings)
    pipeline = DocumentCompressorPipeline(transformers=[filter])
    retriever = ContextualCompressionRetriever(
        base_compressor=pipeline, base_retriever=lotr, 
        k=k_override)
    
    log.info(f"Returning Langchain retrieval object: {retriever}")
    return retriever