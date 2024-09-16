from my_log import log
from sunholo.utils import ConfigManager

# VAC specific imports 

#TODO: Developer to update to their own implementation
from sunholo.vertex import init_vertex, vertex_safety
from vertexai.preview.generative_models import GenerativeModel

#TODO: change this to a streaming VAC function for your use case
def vac_stream(question: str, vector_name:str, chat_history=[], callback=None, **kwargs):

    model = create_model(vector_name)

    # streaming model calls
    response = model.generate_content(question, stream=True)
    for chunk in response:
        try:
            callback.on_llm_new_token(token=chunk.text)
        except ValueError as err:
            callback.on_llm_new_token(token=str(err))
    
    # stream has finished, full response is also returned
    callback.on_llm_end(response=response)
    log.info(f"model.response: {response}")

    metadata = {
        "question": question,
        "vector_name": vector_name,
        "chat_history": chat_history
    }

    return {"answer": response.text, "metadata": metadata}


# TODO: example model setup function
def create_model(vac):
    config = ConfigManager(vac)

    init_vertex()

    # get a setting from the config vacConfig object (returns None if not found)
    model = config.vacConfig("model")

    # Create a gemini-pro model instance
    # https://ai.google.dev/api/python/google/generativeai/GenerativeModel#streaming
    rag_model = GenerativeModel(
        model_name=model or "gemini-1.5-flash",
         safety_settings=vertex_safety()
    )

    return rag_model