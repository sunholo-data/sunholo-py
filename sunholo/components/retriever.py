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
from ..logging import setup_logging
from .vectorstore import pick_vectorstore
from ..utils import load_config_key
from .llm import get_embeddings
from ..utils.gcp import get_gcp_project

from langchain.retrievers import MergerRetriever
from langchain_community.retrievers import GoogleCloudEnterpriseSearchRetriever
# https://python.langchain.com/docs/integrations/retrievers/merger_retriever
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain.retrievers import ContextualCompressionRetriever

logging = setup_logging()

def load_memories(vector_name):
    """
    This function loads memory settings for a given vector name from a configuration file.

    It loads the memory settings from a configuration file using the load_config_key function and logs the loaded memory settings. If no memory settings are found, it logs this information and returns None.

    :param vector_name: The name of the vector for which to load the memory settings.
    :return: The loaded memory settings, or None if no memory settings are found.
    """
    memories = load_config_key("memory", vector_name, filename="config/llm_config.yaml")
    logging.info(f"Found memory settings for {vector_name}: {memories}")
    if len(memories) == 0:
        logging.info(f"No memory settings found for {vector_name}")
        return None

    return memories

def pick_retriever(vector_name, embeddings=None):
    """
    This function creates a list of retrievers based on the memory settings loaded by the load_memories function.

    It first calls the load_memories function to load the memory settings for the vector name. Then it iterates over the memory settings and for each memory, it checks if a vectorstore is specified. If a vectorstore is specified, it picks the vectorstore and creates a retriever for it. If a provider is specified and it is 'GoogleCloudEnterpriseSearchRetriever', it creates a GoogleCloudEnterpriseSearchRetriever. Finally, it merges all the retrievers into a MergerRetriever and returns it.

    :param vector_name: The name of the vector for which to create the retrievers.
    :param embeddings: The embeddings used to pick the vectorstore. Defaults to None.
    :return: The created MergerRetriever, or None if no retrievers were created.
    """
    memories = load_memories(vector_name)

    retriever_list = []
    for memory in memories:  # Iterate over the list
        for key, value in memory.items():  # Now iterate over the dictionary
            logging.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore', None)
            if vectorstore is not None:
                logging.info(f"Found vectorstore {vectorstore}")
                if embeddings is None:
                    embeddings = get_embeddings(vector_name)
                vectorstore = pick_vectorstore(vectorstore, vector_name=vector_name, embeddings=embeddings)
                vs_retriever = vectorstore.as_retriever(search_kwargs=dict(k=3))
                retriever_list.append(vs_retriever)
            
            if value.get('provider', None) == "GoogleCloudEnterpriseSearchRetriever":
                logging.info(f"Found GoogleCloudEnterpriseSearchRetriever {value['provider']}")
                gcp_retriever = GoogleCloudEnterpriseSearchRetriever(
                    project_id=get_gcp_project(),
                    search_engine_id=value["db_id"],
                    location_id=value.get("location", "global"),
                    engine_data_type=1 if value.get("type","unstructured") == "structured" else 0,
                    query_expansion_condition=2
                )
                retriever_list.append(gcp_retriever)
            
            #TODO: more memory stores here

    if len(retriever_list) == 0:
        logging.info(f"No retrievers were created for {memories}")
        return None
        
    lotr = MergerRetriever(retrievers=retriever_list)

    filter_embeddings = get_embeddings(vector_name)
    filter = EmbeddingsRedundantFilter(embeddings=filter_embeddings)
    pipeline = DocumentCompressorPipeline(transformers=[filter])
    retriever = ContextualCompressionRetriever(
        base_compressor=pipeline, base_retriever=lotr, 
        k=3)

    return retriever