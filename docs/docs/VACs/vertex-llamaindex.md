# VertexAI Grounding with LlamaIndex and Google Search

LlamaIndex is available within the [VertexAI platform via a serverless integration](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/rag-api)

Grounding is also available using a [Google Search](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/ground-gemini#ground-gemini-web-python_vertex_ai_sdk)

`sunholo` integrates with this application by providing HTTP endpoints for the indexing or new documents placed within Google Cloud Storage and via streaming or static VAC endpoints.  Whilst only some embedding features are implemented at the moment, the LlamaIndex on VertexAI integration takes care of a lot of aspects such as chunking and embedding, with no server to set up.  This makes it a good choice for quick and low-maintenance RAG applications.

The code for this VAC is available at the [Public VAC GitHub repository](https://github.com/sunholo-data/vacs-public/tree/dev/vertex-genai).

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

You need these `sunholo` modules:

```sh
pip install sunholo[gcp,http]
```

If you want to test using the CLI also install `sunholo[cli]`

e.g

```sh
pip install sunholo[gcp,http,cli]
```

## File Indexing

Once your configuration is loaded within Multivac, embed and index them by adding files to your Google Cloud Storage bucket to have the files indexed, via `llamaindex.import_files.py`.  This supports large amounts of files.

For more details on how to set up indexing, see the [embedding pipeline documentation](../howto/embedding).

## Config

To use LlamaIndex on VertexAI, set up a memory store to send data to:

* `llm` - LlamaIndex on VertexAI is only available on "vertex"
* `model` - Needs to be one of the supported models listed [here](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/rag-api)
* `agent` - `vertex-genai` is the VAC code shown in this example
* `display_name` - for UI integrations
* `description` - for UI integrations
* `grounding` - Set to add Google Search grounding to the context of the answers
* `memory` - configure the `vectorstore` setting to `llamaindex` to trigger sending data to the VertexAI rag corpus.  You can also send data to other memory types, such as `alloydb`.
* `gcp_config` - settings that determine which VertexAI rag instance the data is sent to.  Only available in `us-central1` at the moment.  `rag_id` is the numeric identifier that you get when using `rag.create()` to make the RAG corpus.
* `chunker` - settings to configure on how LlamaIndex splits the data.

```yaml
kind: vacConfig
apiVersion: v1
gcp_config: # reached via vac='global'
  project_id: your-gcp-project
  location: europe-west1
vac:  
  personal_llama:
    llm: vertex
    model: gemini-1.5-pro-preview-0514
    agent: vertex-genai
    display_name: Gemini with grounding via Google Search and LlamaIndex
    description: Using LlamaIndex RAG and Google Search to ground the answers
    grounding:
      google_search: true # if true will use Google Search in grounding results
    memory:
      - llamaindex-native:
          vectorstore: llamaindex
          rag_id: 123123132 # you create this during setup
    gcp_config:
      project_id: your-gcp-project
      location: us-central1   # llamaindex is only available in us-central1 atm
    chunker:
      chunk_size: 1000
      overlap: 200
```

## Test calls

### Locally

Start up the Flask server:

```sh
python vertex-genai/app.py
```

curl query against the URLs:

```shell
curl http://127.0.0.1:8080/vac/personal_llama \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What do you know about MLOps?"
}'

curl http://127.0.0.1:8080/vac/streaming/personal_llama \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What do you know about MLOps?"
}'
```

### Deployed

If deployed on Multivac, you can use the `sunholo` CLI to chat with an instance via a proxy for the authenticated calls:

Assuming the same config as above, which has a [practioners guide to MLOPs](https://services.google.com/fh/files/misc/practitioners_guide_to_mlops_whitepaper.pdf) within its Llamaindex:

```shell
sunholo vac chat personal_llama  

VAC Proxies - `sunholo proxy list`                           
┏━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ VAC          ┃ Port ┃ PID   ┃ URL                   ┃ Local ┃ Logs                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ vertex-genai │ 8080 │ 48434 │ http://127.0.0.1:8080 │ No    │ No log file specified │
└──────────────┴──────┴───────┴───────────────────────┴───────┴───────────────────────┘
╭───────────────────────────────── Gemini with grounding via Google Search and LlamaIndex ─────────────────────────────────╮
│ Starting VAC chat session                                                                                                │
╰────── stream: http://127.0.0.1:8080/vac/streaming/personal_llama invoke: http://127.0.0.1:8080/vac/personal_llama ───────╯
You: what is MLOps?
✺ Thinking...
```

The reply below takes the grounding from LlamaIndex:

```bash
personal_llama: MLOps, short for Machine Learning Operations, is a methodology bridging the gap between machine learning application 
development and their real-world deployment and operation. It aims to streamline and automate the entire lifecycle of an ML 
model, from its initial development to deployment and ongoing maintenance. 

Here's a breakdown of what MLOps encompasses:

* **Standardized Processes:** MLOps establishes standardized workflows and best practices for building, deploying, and 
managing ML systems, ensuring consistency and efficiency.
* **Automation:** It emphasizes automating repetitive tasks within the ML lifecycle, like model training, testing, and 
deployment, to accelerate development and reduce errors.
* **Reliability and Scalability:**  MLOps promotes practices that guarantee the reliability, scalability, and performance of
ML models in production environments. 
* **Continuous Improvement:** By incorporating monitoring, logging, and feedback mechanisms, MLOps enables continuous model 
improvement and adaptation over time.

**In essence, MLOps combines the best of software engineering and machine learning to deliver ML solutions in a robust, 
scalable, and automated manner.** 

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

Testing the Google Search grounding:

```bash
You: what happened this week in the run up to the UK election?
✺ Thinking...

personal_llama: Combining the information provided:

While I cannot access real-time information to confirm specific news from last week, it's likely that news regarding the UK 
general election included:

* **Reform UK launching their campaign in Clacton.** This suggests the party is actively campaigning in specific areas.
* **The Liberal Democrats announcing an NHS funding pledge.**  This indicates parties are revealing key policy points in 
their election manifestos. 
```
