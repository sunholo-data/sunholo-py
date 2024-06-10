try:
    from vertexai.preview import rag
    from vertexai.preview.generative_models import Tool, grounding, GenerationResponse
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

    if not memories:
        return tools
    
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

def print_grounding_response(response):
    """Prints Gemini response with grounding citations."""
    grounding_metadata = response.candidates[0].grounding_metadata

    # Citation indices are in byte units
    ENCODING = "utf-8"
    text_bytes = response.text.encode(ENCODING)

    prev_index = 0
    markdown_text = ""

    sources: dict[str, str] = {}
    footnote = 1
    for attribution in grounding_metadata.grounding_attributions:
        context = attribution.web or attribution.retrieved_context
        if not context:
            log.info(f"Skipping Grounding Attribution {attribution}")
            continue

        title = context.title
        uri = context.uri
        end_index = int(attribution.segment.end_index)

        if uri not in sources:
            sources[uri] = {"title": title, "footnote": footnote}
            footnote += 1

        text_segment = text_bytes[prev_index:end_index].decode(ENCODING)
        markdown_text += f"{text_segment} [[{sources[uri]['footnote']}]]({uri})"
        prev_index = end_index

    if prev_index < len(text_bytes):
        markdown_text += str(text_bytes[prev_index:], encoding=ENCODING)

    markdown_text += "\n## Grounding Sources\n"

    if grounding_metadata.web_search_queries:
        markdown_text += (
            f"\n**Web Search Queries:** {grounding_metadata.web_search_queries}\n"
        )
    elif grounding_metadata.retrieval_queries:
        markdown_text += (
            f"\n**Retrieval Queries:** {grounding_metadata.retrieval_queries}\n"
        )

    for uri, source in sources.items():
        markdown_text += f"{source['footnote']}. [{source['title']}]({uri})\n"
    
    log.info(markdown_text)
    return markdown_text