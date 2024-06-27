# Vertex AI

## Vertex AI Search

Formally called Enterprise Search and AI Search and Conversation, this is a data store chunk version.

Set `vectorstore: vertex_ai_search` to use in your application

```yaml
memory:
    - discovery_engine_vertex_ai_search:
        vectorstore: vertex_ai_search # or 'discovery_engine'
```

### Calling Vertex AI Search

You can use `vertex_ai_search` or `llamaindex` specified below in your Vertex GenAI apps like this:

```python
from sunholo.utils.config import load_config_key
from sunholo.vertex import init_vertex, get_vertex_memories, vertex_safety

from vertexai.preview.generative_models import GenerativeModel, Tool

vac_name = "must_match_your_vacConfig"

# will init vertex client
init_vertex()

# will look in your vacConfig for vertex-ai-search and llamaindex vectorstores
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

The above assumes a vacConfig like this:

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


## LlamaIndex on Vertex AI

To use Llama Index on Vertex AI, set it as a `memory` within your `vacConfig` file.

Set `vectorstore: llamaindex`

```yaml
memory:
    - llamaindex-native:
        vectorstore: llamaindex
        rag_id: 4611686018427387904 
```

See above for code calling your data for RAG.

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
