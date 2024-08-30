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
def vac(question: str, vector_name: str, chat_history=[], **kwargs):
    # Create a callback that does nothing for streaming if you don't want intermediate outputs
    class NoOpCallback:
        def on_llm_new_token(self, token):
            pass
        def on_llm_end(self, response):
            pass

    # Use the NoOpCallback for non-streaming behavior
    callback = NoOpCallback()

    # Pass all arguments to vac_stream and use the final return
    result = vac_stream(
        question=question, 
        vector_name=vector_name, 
        chat_history=chat_history, 
        callback=callback, 
        **kwargs
    )

    return result


# TODO: common model setup to both batching and streaming
def create_model(vac):
    config = ConfigManager(vac)

    init_vertex()
    corpus_tools = get_vertex_memories(config)

    model = config.vacConfig("model")

    # Create a gemini-pro model instance
    # https://ai.google.dev/api/python/google/generativeai/GenerativeModel#streaming
    rag_model = GenerativeModel(
        model_name=model or "gemini-1.5-flash", tools=[corpus_tools]
    )

    return rag_model