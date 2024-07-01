# Creating a grounded Vertex app

This goes through how to make a Vertex AI app with grounding via Google Search.

## Bootstrap

This is common to most VACs:

0. Install via `pip install sunholo`
1. Create a new git repository and browse to the root
1. Run `sunholo init new_project` to create a project called "new_project"
1. This will create a new folder with an example project files.
1. Make your changes to the `vac_service.py` file - specifically the `vac` and `vac_stream` functions
1. Modify the `vacConfig` in `config/vac_config.yaml` with new instances of your VAC.

## vacConfig

This controls the configurations of the different instances that can all re-use the same code you create in the scripts below.  Each `vac` entry lets you create new prompts, features and a unique memory namespaces (e.g. one vector strore per instance)

```yaml
kind: vacConfig
apiVersion: v1
vac:
  my_grounded_vertex:
    llm: vertex
    model: gemini-1.5-pro-preview-0514
    model_quick: gemini-1.5-flash-001
    agent: vertex-genai # the underlying cloud run application
    display_name: Grounded Google
    display_name: Gemini with grounding via Google Search
    grounding:
      google_search: true
#... add new instances here
```

## vac_service.py

This is the guts of your GenAI application.  You can optionally create a batch `vac()` function and/or a `vac_stream()` function that will be invoked when calling the VAC endpoints.  Additional arguments will be passed to help with common GenAI application tasks.  

Here is an example file that is used when doing `sunholo init new_project`

```python
from sunholo.logging import setup_logging
from sunholo.utils.config import load_config_key

# VAC specific imports
from sunholo.vertex import init_vertex, get_google_search_grounding
from vertexai.preview.generative_models import GenerativeModel

log = setup_logging("template")

#TODO: change this to a streaming VAC function
def vac_stream(question: str, vector_name, chat_history=[], callback=None, **kwargs):

    grounded_model = create_model(vector_name)

    # streaming model calls
    response = grounded_model.generate_content(question, stream=True)

    chunks = ""
    for chunk in response:
        try:
            callback.on_llm_new_token(token=chunk.text)
            chunks += chunk.text
        except ValueError as err:
            callback.on_llm_new_token(token=str(err))
    
    callback.on_llm_end(response=response)

    chat_history.append({
        "role":"ai", "content": chunks
    })

    metadata = {
        "chat_history": chat_history
    }

    return {"answer": chunks, "metadata": metadata}


#TODO: change this to a batch VAC function
def vac(question: str, vector_name, chat_history=[], **kwargs):

    grounded_model = create_model(vector_name)

    response = grounded_model.generate_content(question)

    log.info(f"Got response: {response}")

    return {"answer": response.text}


# TODO: common model setup to both batching and streaming
def create_model(vector_name):
    gcp_config = load_config_key("gcp_config", vector_name=vector_name, kind="vacConfig")

    init_vertex(gcp_config)
 
    model = load_config_key("model", vector_name=vector_name, kind="vacConfig")
    google_search = get_google_search_grounding(vector_name)

    # Create a gemini-pro model instance
    # https://ai.google.dev/api/python/google/generativeai/GenerativeModel#streaming
    rag_model = GenerativeModel(
        model_name=model or "gemini-1.0-pro-002", tools=[google_search]
    )

    return rag_model
```

### Streaming

As a minimum the streaming function needs these arguments:

```python
def vac_stream(question: str, vector_name, chat_history=[], callback=None, **kwargs):
...
```

* `question`: the text of the question typcially sent by the user
* `vector_name`: the vector_name is an instance of your VAC, tailored to its own namespace.  AT least one is required per VAC, but you can many with different variations of prompt, model etc.
* `chat_history`: A list of chat history messages
* `callback`: Do not add anything here, it will be used by the VAC to print out the streaming chat tokens.
* `kwargs`: Any other additional arguments you may need, but can also include some listed below:
  - `image_uri`: the image URI location for image/video models
  - `mime`: the MIME type of the URI location
  - #TODO: more

### Images/Videos

Images can be automatically inserted into your request arguments.

Make a request to upload a new image via a POST form request.  The VAC will then upload that image to a Google Cloud Storage bucket, and return the URL, or if say the endpoint accepts base64 images pass that through.

The image and mime type are then available to your VACs in the `kwargs` via `uri` and `mime`

```python
def vac_stream(question: str, vector_name: str, chat_history=[], callback=None, **kwargs):

...
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
...
```