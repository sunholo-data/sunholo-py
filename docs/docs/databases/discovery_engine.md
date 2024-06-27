# Vertex AI Search / Discovery Engine

This has had a few names etc. Vertex AI Search and Conversation but its this service: https://cloud.google.com/enterprise-search

Not to be confused with [Vertex AI Vector Search](https://cloud.google.com/vertex-ai/docs/vector-search/overview) which is the new name for Matching Engine (confused yet?)

## Serverless chunking

Regardless, it is a very low code way to create RAG apps.  It takes care of the chunking and indexing meaning you can just send in your documents and use them within your GenAI apps smoothly.

An example config is shown below:

```yaml
kind: vacConfig
apiVersion: v1
vac:
  sample_vector:
    llm: vertex
    agent: edmonbrain
    memory:
      - discovery_engine_vertex_ai_search:
          vectorstore: vertex_ai_search # or discovery_engine
```

Since no chunking is necessary, documents are not indexed via the embedding service, but directly sent to the Vertex AI Search data store, with the same id as the VAC name e.g. sample_vector in above example.  Make new Data Stores by creating new VACs.