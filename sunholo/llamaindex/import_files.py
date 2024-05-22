
try:
    from vertexai.preview import rag
    from vertexai.preview.generative_models import GenerativeModel, Tool
    import vertexai
except ImportError:
    rag = None

from ..logging import log
from ..utils.config import load_config_key

# Create a RAG Corpus, Import Files

def init_vertex(gcp_config):
    """
    Initializes the Vertex AI environment using the provided Google Cloud Platform configuration.

    This function configures the Vertex AI API session with specified project and location details
    from the gcp_config dictionary. It is essential to call this function at the beginning of a session
    before performing any operations related to Vertex AI.

    Parameters:
        gcp_config (dict): A dictionary containing the Google Cloud Platform configuration with keys:
            - 'project_id': The Google Cloud project ID to configure for Vertex AI.
            - 'location': The Google Cloud region to configure for Vertex AI.

    Raises:
        KeyError: If the necessary keys ('project_id' or 'location') are missing in the gcp_config dictionary.
        ModuleNotFoundError: If the Vertex AI module is not installed and needs to be installed via pip.

    Example:
    ```python
    gcp_config = {
         'project_id': 'your-project-id',
         'location': 'us-central1'
    }
    init_vertex(gcp_config)
    # This will initialize the Vertex AI session with the provided project ID and location.

    Note:
        Ensure that the 'vertexai' module is installed and correctly configured before calling this function.
        The function assumes that the required 'vertexai' library is available and that the logging setup is already in place.
    """
    if not rag:
        log.error("Need to install vertexai module via `pip install google-cloud-aiplatform`")
    
    # Initialize Vertex AI API once per session
    project_id = gcp_config.get('project_id')
    location = gcp_config.get('location')
    vertexai.init(project=project_id, location=location)

def get_corpus(gcp_config):
    project_id = gcp_config.get('project_id')
    location = gcp_config.get('location')
    rag_id = gcp_config.get('rag_id')
    if not project_id:
        raise ValueError("Need config.gcp.project_id to configure llamaindex on VertexAI")
    if not rag_id:
        raise ValueError("Need config.gcp.rag_id to configure llamaindex on VertexAI.  Create via `rag.create_corpus(display_name=vector_name, description=description)`")

    corpus_name = f"projects/{project_id}/locations/{location}/ragCorpora/{rag_id}"  

    try:
        return rag.get_corpus(name=corpus_name)
    except Exception as err:
        #log.warning(f"Failed to fetch corpus - creating new corpus {str(err)}")
        # it does not create a unique corpus, display_name can be in multiple rag_ids
        #try:
        #    corpus = rag.create_corpus(display_name=vector_name, description=description)
        #except Exception as err:
        #    log.error(f"Failed to get or create corpus {str(err)}")
        raise ValueError(f"Failed to get or create corpus: {str(err)}")
    

def do_llamaindex(message_data, metadata, vector_name):
    """
    Configures and manages the corpus for a VertexAI project using the specified vector name
    by importing message data from Google Cloud Storage or Google Drive URLs.

    This function loads configuration from a YAML file, initializes a Vertex AI environment,
    and either fetches an existing corpus or creates a new one if it doesn't exist.
    It supports importing files directly from cloud storage links.

    Parameters:
        message_data (str): The URL to the data on Google Cloud Storage or Google Drive that needs to be imported to the corpus.
        metadata (dict): Additional metadata not explicitly used in this function but might be needed for extended functionality.
        vector_name (str): The name of the vector (and corpus) which will be used to locate and configure the specific settings from the configuration files.

    Raises:
        ValueError: If the necessary configurations for GCP or project ID are not found, or if the corpus could not be established.
        NotImplementedError: If the data is not from supported sources (Google Cloud Storage or Google Drive).

    Example:
    ```python
    message_data = "gs://bucket_name/path_to_file.txt"
    metadata = {"user": "admin"}
    vector_name = "example_vector"
    response = do_llamaindex(message_data, metadata, vector_name)
    print(response)
    # Imported file to corpus: {'status': 'success'}
    ```
    """
    gcp_config = load_config_key("gcp_config", vector_name=vector_name, filename = "config/llm_config.yaml")
    if not gcp_config:
        raise ValueError(f"Need config.{vector_name}.gcp_config to configure llamaindex on VertexAI")

    init_vertex(gcp_config)
    corpus = get_corpus(gcp_config)
    #display_name = load_config_key("display_name", vector_name=vector_name, filename="config/llm_config.yaml")
    #description = load_config_key("description", vector_name=vector_name, filename="config/llm_config.yaml")

    try:
        corpura = rag.list_corpora()
        log.info(f"Corpora: {corpura} - {type(corpura)}")
    except Exception as err:
        log.warning(f"Could not list any corpora - {str(err)}")

    log.info(f"Found llamaindex corpus: {corpus}")

    # native support for cloud storage and drive links
    chunker_config = load_config_key("chunker", vector_name=vector_name, filename="config/llm_config.yaml")

    if message_data.startswith("gs://") or message_data.startswith("https://drive.google.com"):
        log.info(f"rag.import_files for {message_data}")
        response = rag.import_files(
            corpus_name=corpus.name,
            paths=[message_data],
            chunk_size=chunker_config.get("chunk_size"),  # Optional
            chunk_overlap=chunker_config.get("overlap"),  # Optional
        )
        log.info(f"Imported file to corpus: {response} with metadata: {metadata}")

        metadata["source"] = message_data
        return metadata
    
    else:
        raise NotImplementedError("Only gs:// and https://drive data is supported")
        # write text to file and upload it
        # TODO(developer): Update and un-comment below lines
        # project_id = "PROJECT_ID"
        # corpus_name = "projects/{project_id}/locations/us-central1/ragCorpora/{rag_corpus_id}"
        # path = "path/to/local/file.txt"
        # display_name = "file_display_name"
        # description = "file description"

        # Initialize Vertex AI API once per session
        #path = 'path/to/local/file.txt'

        # Write the message_data to a file
        #with open(path, 'w') as file:
        #    file.write(message_data)

        #rag_file = rag.upload_file(
        #    corpus_name=corpus_name,
        #    path=path,
        #    display_name=display_name,
        #    description=description,
        #)


def llamaindex_chunker_check(message_data, metadata, vector_name):
    # llamaindex handles its own chunking/embedding
    memories = load_config_key("memory", vector_name=vector_name, filename = "config/llm_config.yaml")
    total_memories = len(memories)
    llama = None
    for memory in memories:  # Iterate over the list
        for key, value in memory.items():  # Now iterate over the dictionary
            log.info(f"Found memory {key}")
            vectorstore = value.get('vectorstore')
            if vectorstore:
                log.info(f"Found vectorstore {vectorstore}")
                if vectorstore == "llamaindex":
                    # https://cloud.google.com/vertex-ai/generative-ai/docs/llamaindex-on-vertexai
                    log.info(f"llamaindex on vertex indexing for {vector_name}")
                    llama = do_llamaindex(message_data, metadata, vector_name)
                    log.info(f"Processed llamaindex: {llama}")

    # If llamaindex is the only entry, return
    if llama and total_memories == 1:

        return llama
    
    elif llama:
        log.info("Llamaindex found but not the only memory, continuing with other processes.")

        return None