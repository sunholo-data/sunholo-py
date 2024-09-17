try:
    from vertexai.preview import rag
    from vertexai.preview.generative_models import Tool, grounding
except ImportError:
    rag = None

from ..custom_logging import log
from ..components import load_memories
from ..llamaindex.get_files import fetch_corpus
from ..llamaindex.llamaindex_class import LlamaIndexVertexCorpusManager
from ..discovery_engine.discovery_engine_client import DiscoveryEngineClient
from ..utils.gcp_project import get_gcp_project
from ..utils import ConfigManager

def get_vertex_memories(config:ConfigManager):
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

    gcp_config = config.vacConfig("gcp_config")

    if not rag:
        raise ValueError("Need to install vertexai module via `pip install sunholo[gcp]`")
    
    global_location = gcp_config.get('location')

    memories = load_memories(config=config)
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
                project_id = value.get('project_id') or gcp_config.get('project_id')
                location = value.get('location') or gcp_config.get('location')

                if rag_id:
                    log.info("Using rag_id for using vectorstore: llamaindex")
                    try:
                        corpus = fetch_corpus(
                                project_id=project_id or get_gcp_project(),
                                location=location or global_location,
                                rag_id=rag_id
                            )
                    except Exception as err:
                        log.error(f"Skipping - No rag found for {rag_id=} - {str(err)}")
                        continue
                else:
                    log.info(f"Using display_name {config.vector_name} to derive rag_id")
                    manager = LlamaIndexVertexCorpusManager(project_id=project_id, location=location)
                    corpus = manager.find_corpus_from_list(config.vector_name)

                try:
                    corpus_tool = Tool.from_retrieval(
                        retrieval=rag.Retrieval(
                            source=rag.VertexRagStore(
                                rag_corpora=[corpus.name],  # Currently only 1 corpus is allowed.
                                similarity_top_k=10,  # Optional
                            ),
                        )
                    )
                    tools.append(corpus_tool)
                except Exception as err:
                    log.error(f"Failed to fetch vertex.rag: {str(err)} - skipping")
                    continue

            elif vectorstore == "discovery_engine" or vectorstore == "vertex_ai_search":

                try:
                    project_id = value.get('project_id') or get_gcp_project()
                    if value.get('chunks'):
                        log.warning("Data stores for chunks do not work with Tools yet, call data store directly instead")
                        continue

                    if value.get('read_only'):
                        new_vector_name = value.get('vector_name')
                        if not new_vector_name:
                            log.warning("read_only specified but no new vector_name to read from")
                        vector_name = new_vector_name

                    de = DiscoveryEngineClient(vector_name, project_id=project_id)
                    log.info(f"Found vectorstore {vectorstore}")

                    data_store_path = f"{de.data_store_path()}/dataStores/{vector_name}"
                    corpus_tool = Tool.from_retrieval(
                        grounding.Retrieval(grounding.VertexAISearch(datastore=data_store_path))
                    )
                    tools.append(corpus_tool)
                except Exception as err:
                    log.error(f"Failed to fetch DiscoveryEngine grounding - {str(err)} - skipping")
                    continue
                

    if not tools:
        log.warning("No Vertex corpus configurations could be found")
    
    return tools

def get_google_search_grounding(vector_name:str=None, config:ConfigManager=None):
    if config is None:
        if vector_name is None:
            raise ValueError("Must specify one of vector_name or config")
        config = ConfigManager(vector_name)

    # can't have this and llamaindex memories?
    tools = config.vacConfig("tools")
    if tools and tools.get("google_search"):
        gs_tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())
        log.info(f"Got Search Tool: {gs_tool}")
        return gs_tool
    
    log.info(f"No google search config available for {vector_name}")
    return None

def print_grounding_response(response):
    """Prints Gemini response with grounding citations."""
    grounding_metadata = response.candidates[0].grounding_metadata

    # Citation indices are in byte units
    ENCODING = "utf-8"
    text_bytes = response.text.encode(ENCODING)

    prev_index = 0
    markdown_text = ""

    for grounding_support in grounding_metadata.grounding_supports:
        text_segment = text_bytes[
            prev_index : grounding_support.segment.end_index
        ].decode(ENCODING)

        footnotes_text = ""
        for grounding_chunk_index in grounding_support.grounding_chunk_indices:
            footnotes_text += f"[{grounding_chunk_index + 1}]"

        markdown_text += f"{text_segment} {footnotes_text}\n"
        prev_index = grounding_support.segment.end_index

    if prev_index < len(text_bytes):
        markdown_text += str(text_bytes[prev_index:], encoding=ENCODING)

    markdown_text += "\n----\n## Grounding Sources\n"

    if grounding_metadata.web_search_queries:
        markdown_text += (
            f"\n**Web Search Queries:** {grounding_metadata.web_search_queries}\n"
        )
    elif grounding_metadata.retrieval_queries:
        markdown_text += (
            f"\n**Retrieval Queries:** {grounding_metadata.retrieval_queries}\n"
        )

    for index, grounding_chunk in enumerate(
        grounding_metadata.grounding_chunks, start=1
    ):
        context = grounding_chunk.web or grounding_chunk.retrieved_context
        if not context:
            print(f"Skipping Grounding Chunk {grounding_chunk}")
            continue
        markdown_text += "### Grounding Chunks\n"

        markdown_text += f"{index}. [{context.title}]({context.uri})\n"

    return {"markdown_text": markdown_text, 
            "search_entry_point": grounding_metadata.search_entry_point.rendered_content if grounding_metadata.search_entry_point else ""}
