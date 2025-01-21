from my_log import log
from sunholo.utils import ConfigManager

# VAC specific imports 

#TODO: Developer to update to their own implementation
from sunholo.genai import init_genai, genai_safety
import google.generativeai as genai

#TODO: change this to a streaming VAC function for your use case
def vac_stream(question: str, vector_name:str, chat_history=[], callback=None, **kwargs):

    model = create_model(vector_name)

    # create chat history for genai model
    # https://ai.google.dev/api/generate-content
    contents = []
    for human, ai in chat_history:
        if human:
            contents.append({"role":"user", "parts":[{"text": human}]})
        
        if ai:
            contents.append({"role":"model", "parts":[{"text": ai}]})


    # the user question at the end of contents list
    contents.append({"role":"user", "parts":[{"text": question}]})

    log.info(contents)
    # streaming model calls
    response = model.generate_content(contents, stream=True)
    chunks=""
    for chunk in response:
        if chunk and chunk.text:
            try:
                callback.on_llm_new_token(token=chunk.text)
                chunks += chunk.text
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

    # to not return this dict at the end of the stream, pass stream_only: true in request
    return {"answer": chunks, "metadata": metadata}


# TODO: example model setup function
def create_model(vac):
    config = ConfigManager(vac)

    init_genai()

    # get a setting from the config vacConfig object (returns None if not found)
    model = config.vacConfig("model")

    # Create a gemini-flash model instance
    # https://ai.google.dev/api/python/google/generativeai/GenerativeModel#streaming
    genai_model = genai.GenerativeModel(
        model_name=model or "gemini-1.5-flash",
         safety_settings=genai_safety()
    )

    return genai_model
