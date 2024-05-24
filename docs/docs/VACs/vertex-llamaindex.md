# LlamaIndex on VertexAI

LlamaIndex is available within the VertexAI platform via a serverless integration - see here: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/rag-api

`sunholo` integrates with this application by providing HTTP endpoints for the indexing or new documents placed within Google Cloud Storage and via streaming or static VAC endpoints.  Whilst only some embedding features are implemented at the moment, the LlamaIndex on VertexAI integration takes care of a lot of aspects such as chunking and embedding, with no server to set up.  This makes it a good choice for quick and low-maintenance RAG applications.

## Setup

You need a corpus ID created when you make one (only available via API at the moment):

```python
import vertexai
from vertexai.preview import rag

vertexai.init(project=<project_id>, location="us-central1")
corpus = rag.create_corpus(display_name=..., description=...)
print(corpus)
```

Use the project_id, location and corpus_id within your config below.

## File Indexing

Once your configuration is loaded within Mulitvac, embed and index them by adding files to your Google Cloud Storage bucket to have the files indexed, via [`llamaindex.import_files.py`](../sunholo/llamaindex.import_files).  This supports large amounts of files.

## Config

To use LlamaIndex on VertexAI, set up a memory store to send data to:

* `llm` - LlamaIndex on VertexAI is only available on "vertex"
* `model` - Needs to be one of the supported models listed [here](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/rag-api)
* `agent` - `vertex-genai` is the VAC code shown in this example
* `display_name` - for UI integrations
* `description` - for UI integrations
* `memory` - configure the `vectorstore` setting to `llamaindex` to trigger sending data to the VertexAI rag corpus.  You can also send data to other memory types, such as `alloydb`.
* `gcp_config` - settings that determine which VertexAI rag instance the data is sent to.  Only available in `us-central1` at the moment.  `rag_id` is the numeric identifier that you get when using `rag.create()` to make the RAG corpus.
* `chunker` - settings to configure on how LlamaIndex splits the data.

```yaml
kind: vacConfig
apiVersion: v1
vac:
  personal_llama:
    llm: vertex
    model: gemini-1.5-pro-preview-0514
    agent: vertex-genai
    display_name: LlamaIndex via Vertex AI
    description: Use LlamaIndex on VertexAI via its vertex.rag integration
    memory:
      - llamaindex-native:
          vectorstore: llamaindex
    gcp_config:
      project_id: llamaindex_project
      location: us-central1 # only here at the moment
      rag_id: 12341232323 # created via rag.create for now     
    chunker:
      chunk_size: 1000
      overlap: 200