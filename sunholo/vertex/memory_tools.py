try:
    from vertexai.preview import rag
    from vertexai.preview.generative_models import Tool, grounding
except ImportError:
    rag = None

from ..logging import log
from ..utils.config import load_config_key
from ..components import load_memories
from ..llamaindex.get_files import fetch_corpus

def get_vertex_memories(vector_name):
    """
    Retrieves a LlamaIndex corpus from Vertex AI based on the provided Google Cloud configuration.
    
    This function constructs a corpus name using project details from the configuration and attempts
    to fetch the corresponding corpus. If the corpus cannot be retrieved, it raises an error.
    
    Parameters:
    - vector_name: The name of the of VAC
    
    Returns:
    - List of corpus objects fetched from Vertex AI.
    
    Raises:
    - ValueError: If any of the required configurations (project_id, location, or rag_id) are missing,
      or if the corpus cannot be retrieved.

    Example:
    ```python

    # Fetch the corpus
    try:
        corpus = get_corpus("edmonbrain")
        print("Corpus fetched successfully:", corpus)
    except ValueError as e:
        print("Error fetching corpus:", str(e))
    ```
    """
    gcp_config = load_config_key("gcp_config", vector_name=vector_name, kind="vacConfig")

    if not rag:
        raise ValueError("Need to install vertexai module via `pip install sunholo[gcp]`")
    
    global_project_id = gcp_config.get('project_id')
    global_location = gcp_config.get('location')
    global_rag_id = gcp_config.get('rag_id')
    global_data_store_id = gcp_config.get('data_store_id')

    memories = load_memories(vector_name)
    tools = []
    for memory in memories:
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore == "llamaindex":
                log.info(f"Found vectorstore {vectorstore}")
                rag_id = value.get('rag_id')
                project_id = gcp_config.get('project_id')
                location = gcp_config.get('location')
                corpus = fetch_corpus(
                    project_id=project_id or global_project_id,
                    location=location or global_location,
                    rag_id=rag_id or global_rag_id
                )
                corpus_tool = Tool.from_retrieval(
                    retrieval=rag.Retrieval(
                        source=rag.VertexRagStore(
                            rag_corpora=[corpus.name],  # Currently only 1 corpus is allowed.
                            similarity_top_k=10,  # Optional
                        ),
                    )
                )
                tools.append(corpus_tool)
            elif vectorstore == "vertexai_agent_builder":
                log.info(f"Found vectorstore {vectorstore}")
                data_store_id = value.get('data_store_id') or global_data_store_id
                project_id = gcp_config.get('project_id') or global_project_id
                location = gcp_config.get('location') or global_location
                data_store_path=f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}"

                corpus_tool = Tool.from_retrieval(
                    grounding.Retrieval(grounding.VertexAISearch(datastore=data_store_path))
                )
                tools.append(corpus_tool)
                

    if not tools:
        log.warning("No llamaindex Vertex corpus configurations could be found")
    
    return tools
