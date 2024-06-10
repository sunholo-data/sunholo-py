# Vertex AI


## Vertex AI Agent Builder

To use Agent Builder, set it as a `memory` within your `vacConfig` file.  

Set `vectorstore: vertexai_agent_builder`

```yaml
memory:
    - agent_data_store:
        vectorstore: vertexai_agent_builder
        data_store_id: 1231231231231
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

