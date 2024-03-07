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
    memories = load_config_key("memory", vector_name, filename="config/llm_config.yaml")
    logging.info(f"Found memory settings for {vector_name}: {memories}")
    if len(memories) == 0:
        logging.info(f"No memory settings found for {vector_name}")
        return None

    return memories

def pick_retriever(vector_name, embeddings=None):

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
