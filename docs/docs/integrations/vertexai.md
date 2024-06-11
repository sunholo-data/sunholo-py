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

