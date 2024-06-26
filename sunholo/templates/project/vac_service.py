from sunholo.logging import setup_logging
from sunholo.utils.config import load_config_key

# VAC specific imports
from sunholo.vertex import init_vertex, get_vertex_memories
from vertexai.preview.generative_models import GenerativeModel

log = setup_logging("template")

#TODO: change this to a streaming VAC function
def vac_stream(question: str, vector_name, chat_history=[], callback=None, **kwargs):

    rag_model = create_model(vector_name)

    # example of image/video processing
    url = None
    if kwargs.get('image_uri'):
        log.info(f"Got image_url: {kwargs.get('image_url')}")
        url = kwargs["image_uri"]
    else:
        log.debug("No image_uri found")

    mime = None
    if kwargs.get('mime'):
        log.info(f"Got mime: {kwargs.get('image_url')}")
        mime = kwargs["mime"]
    else:
        log.debug("No mime found")

    # streaming model calls
    response = rag_model.generate_content(question, stream=True)
    for chunk in response:
        try:
            callback.on_llm_new_token(token=chunk.text)
        except ValueError as err:
            callback.on_llm_new_token(token=str(err))
    
    callback.on_llm_end(response=response)
    log.info(f"rag_model.response: {response}")

    metadata = {
        "chat_history": chat_history
    }

    return {"answer": response.text, "metadata": metadata}



#TODO: change this to a batch VAC function
def vac(question: str, vector_name, chat_history=[], **kwargs):

    rag_model = create_model(vector_name)

    response = rag_model.generate_content(question)

    log.info(f"Got response: {response}")

    return {"answer": response.text}


# TODO: common model setup to both batching and streaming
def create_model(vector_name):
    gcp_config = load_config_key("gcp_config", vector_name=vector_name, kind="vacConfig")
    if not gcp_config:
        raise ValueError(f"Need config.{vector_name}.gcp_config to configure XXXX on VertexAI")

    init_vertex(gcp_config)
    corpus_tools = get_vertex_memories(vector_name)

    model = load_config_key("model", vector_name=vector_name, kind="vacConfig")

    # Create a gemini-pro model instance
    # https://ai.google.dev/api/python/google/generativeai/GenerativeModel#streaming
    rag_model = GenerativeModel(
        model_name=model or "gemini-1.0-pro-002", tools=[corpus_tools]
    )

    return rag_model