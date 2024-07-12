# Vertex AI

## Vertex AI Extensions

[Vertex AI Extensions](https://cloud.google.com/vertex-ai/generative-ai/docs/extensions/overview) are API endpoints your GenAI applications can use to import data not within the model.  Extensions often wrap another API.  

An example is the Code Extension, which lets you execute code in your GenAI workflow. 

Since each VAC running has its own API endpoints, they are candidates for becoming Vertex AI Extensions to be called from other VACs or other GenAI applications not running upon Multivac Cloud.  Vertex AI Extensions have different authentication options ranging from free to an API key or OAuth2.  

The `VertexAIExtensions` class provides methods for executing, creating and deploying Vertex AI extensions. 

Set `extensions` within your `vacConfig` to use specific extensions in your VAC:

```yaml
  my_extension_powered_vac:
    llm: vertex
    model: gemini-1.5-pro-001
    agent: vertex-genai
    extensions:
      - operation_id: post_edmonbrain_invoke
        vac: edmonbrain # optional - if extension is calling a vac then this is used to determine the URL for the extension
        extension_display_name: 'Edmonbrain Database' # specify this or extension_id
        #extension_id: 123123123
        operation_params: # helps get_extension_content() to know what schema will send in data and how to parse it out its reply
          output:
            answer: "output.content"  # which key to use for question
            metadata: "output.metadata"  # which key to use for metadata
          input:
            question: ""  # Placeholder for the question parameter
            chat_history: []  # Optional chat history
            # other input parameters as needed by your extension
            animal: ""
```

You could then fetch data from the Vertex AI Extension from within your app using the helper function [get_extension_content()](../sunholo/vertex/extensions_call)

```python
from sunholo.vertex import get_extension_content
from sunholo.utils import ConfigManager

config = ConfigManager('my_extension_powered_vac')
question = "What is in my database that talks about kittens?")

# maybe other params your extension handles i.e. 'animal'
extension_content = get_extension_content(question, config=config, animal="cat")
```

### VertexAIExtensions()

The underlying [VertexAIExtensions()](../sunholo/vertex/extensions_class) class has methods to aid creating extensions and executing them. See its documentation for more information.

## Vertex AI Search

Formally called Enterprise Search and AI Search and Conversation, this is a data store chunk version.

Set `vectorstore: vertex_ai_search` to use in your application

```yaml
memory:
    - discovery_engine_vertex_ai_search:
        vectorstore: vertex_ai_search # or 'discovery_engine'
```

## LlamaIndex on Vertex AI

To use Llama Index on Vertex AI, set it as a `memory` within your `vacConfig` file.

Set `vectorstore: llamaindex`

```yaml
memory:
    - llamaindex-native:
        vectorstore: llamaindex
        rag_id: 4611686018427387904 
```


### Calling Vertex AI Search and LlamaIndex

First add `vectorstore: llamaindex` and/or `vectorstore: vertex_ai_search` to your `vacConfig` file:

```yaml
kind: vacConfig
apiVersion: v1
vac:
  personal_llama:
    llm: vertex
    model: gemini-1.5-pro-preview-0514
    agent: vertex-genai
    display_name: Gemini with grounding via LlamaIndex and Vertex AI Search
    memory:
      - llamaindex-native:
          vectorstore: llamaindex
          rag_id: 4611686018427387904  # created via cli beforehand
      - discovery_engine_vertex_ai_search:
          vectorstore: vertex_ai_search # or discovery_engine
```

Then you can call those memory types (`vertex_ai_search` or `llamaindex`) in your Vertex GenAI apps like this:

```python
from sunholo.utils.config import load_config_key
from sunholo.vertex import init_vertex, get_vertex_memories, vertex_safety

from vertexai.preview.generative_models import GenerativeModel, Tool

vac_name = "must_match_your_vacConfig"

# will init vertex client
init_vertex()

# get_vertex_memories() will look in your vacConfig for vertex-ai-search and llamaindex vectorstores
# Fetches a Vertex AI Search chunked memory (Discovery Engine)
# also fetches a LlamaIndex chunked memory (LlamaIndexc on Vertex)
corpus_tools = get_vertex_memories(vac_name)

# load model from config
model = load_config_key("model", vac_name, kind="vacConfig")

# use vertex Generative model with your tools
rag_model = GenerativeModel(
    model_name=model or "gemini-1.5-flash-001", 
    tools=corpus_tools,
)

# call the model
response = rag_model.generate_content(contents, 
                                        safety_settings=vertex_safety(),
                                        stream=True)
for chunk in response:
    print(chunk)

```

### Calling Vertex AI Search via Langchain

The above example used the `vertex` python library, but you can use Vertex AI Search from any python script.  

> LlamaIndex on Vertex can't be used from non-Vertex framworks, but you can deploy a native LlamaIndex VAC and use it instead - perhaps via Vertex AI Extensions

A popular GenAI framework is Langchain.

To use Vertex AI Search within Langchain, the [`DiscoveryEngineClient`](../sunholo/discovery_engine/discovery_engine_client/) can be used to import or export chunks from the Vertex AI Search data store.

> DiscoveryEngine is the old name for Vertex AI Search

An example for a `vac_service.py` file is below, based of a [Langchain QA Chat to docs tutorial](https://python.langchain.com/v0.2/docs/how_to/qa_chat_history_how_to).

```python
from sunholo.components import pick_retriever, get_llm, get_embeddings
from sunholo.discovery_engine.discovery_engine_client import DiscoveryEngineClient
from sunholo.utils.gcp_project import get_gcp_project
from sunholo.utils.parsers import escape_braces

def vac(question: str, vector_name, chat_history=[], **kwargs):

    llm = get_llm(vector_name)
    embeddings = get_embeddings(vector_name)
    retriever = pick_retriever(vector_name, embeddings=embeddings)
    intro_prompt = load_prompt_from_yaml("intro", prefix=vector_name)

    # create data store client, that has the vector_name VAC as its id
    de = DiscoveryEngineClient(vector_name, project_id=get_gcp_project())

    chunks = de.get_chunks(question)
    chunk_prompt = intro_prompt.format(context=chunks)

    # we stuff chunks into a langchain prompt that may contain { } 
    # so use escape_braces() so it doesn't break langchain promptTemplate
    chunked_prompt = escape_braces(chunk_prompt) + "\n{context}\nQuestion:{input}\nYour Answer:\n"

    message_tuples = [
        ("system", "You are an assistant bot who is very helpful in your answers"),
        ("human", {"type": "text", "text": chunked_prompt})
    ]

    prompt = ChatPromptTemplate.from_messages(message_tuples)

    summarise_prompt   = PromptTemplate.from_template(load_prompt_from_yaml("summarise", prefix=vector_name))
    
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, summarise_prompt
    )

    chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    response = chain.invoke({"input": question, "chat_history": chat_history})

    return {"answer": response}
```


## Vertex Model Garden

To use GenAI model's deployed to Vertex Model Garden, you can set your 'llm' config and supply an `endpoint_id`

```yaml
vac_model_garden:
    llm: model_garden
    gcp_config:
        project_id: model_garden_project
        endpoint_id: 12345678
        location: europe-west1
```
