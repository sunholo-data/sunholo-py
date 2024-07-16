from my_log import log
from sunholo.utils import ConfigManager

# VAC specific imports 

#TODO: Developer to update to their own implementation
from sunholo.vertex import init_vertex, get_vertex_memories
from vertexai.preview.generative_models import GenerativeModel

#TODO: change this to a streaming VAC function
def vac_stream(question: str, vector_name, chat_history=[], callback=None, **kwargs):

    rag_model = create_model(vector_name)

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
def create_model(vac):
    config = ConfigManager(vac)

    gcp_config = config.vacConfig("gcp_config")
    if not gcp_config:
        raise ValueError(f"Need config.{vac}.gcp_config to configure XXXX on VertexAI")

    init_vertex(gcp_config)
    corpus_tools = get_vertex_memories(vac)

    model = config.vacConfig("model")

    # Create a gemini-pro model instance
    # https://ai.google.dev/api/python/google/generativeai/GenerativeModel#streaming
    rag_model = GenerativeModel(
        model_name=model or "gemini-1.0-pro-002", tools=[corpus_tools]
    )

    return rag_model