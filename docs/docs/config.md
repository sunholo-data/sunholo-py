# Config files

A main aim for the `sunholo` library is to have as much of the functionality needed for GenAI apps available via configuration files, rather than within the code.

This allows you to set up new instances of GenAI apps quickly, and experiment with new models, vectorstores and other features.  

There are various config files available that control different features such as VAC behaviour and user access.  This is very much still a work in progress so the format may change in the future.

## llm_config.yaml

This is the main day to day configuration file that is used to set LLMs, databases and VAC tags.  An example is shown here:

```yaml
pirate_speak:
  llm: openai
  agent: langserve
  display_name: Pirate Speak
  tags: ["free"]
  avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
  description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that will repeat back what you say but in a pirate accent.  Ooh argh me hearties!  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.
csv_agent:
  llm: openai
  agent: langserve
  display_name: Titanic
  tags: ["free"]
  avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
  description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that lets you ask questions over structured data like a database.  In this case, a local database contains statistics from the Titanic disaster passengers.  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.
rag_lance:
  llm: openai
  agent: langserve
  display_name: Simple RAG
  tags: ["free"]
  avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
  description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that lets you ask questions over unstructured data.
  memory:
    - lancedb-vectorstore:
        vectorstore: lancedb
        provider: LanceDB 
finetuned_model:
  llm: model_garden
  agent: langserve
  gcp_config:
    project_id: model_garden_project
    endpoint_id: 12345678
    location: europe-west1
image_talk:
  llm: vertex
  model: gemini-1.0-pro-vision
  agent: langserve
  upload: 
    mime_types:
      - image
  display_name: Talk to Images
  tags: ["free"]
  avatar_url: https://avatars.githubusercontent.com/u/1342004?s=200&v=4
  description: A picture is worth a thousand words, so upload your picture and ask your question to the Gemini Pro Vision model.  Images are remembered for your conversation until you upload another.  This offers powerful applications, which you can get a feel for via the [Gemini Pro Vision docs](https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal/design-multimodal-prompts) 
eduvac:
  llm: anthropic
  model: claude-3-opus-20240229
  agent: eduvac # needs to match multivac service name
  agent_type: langserve
  display_name: Edu-VAC
  tags: ["free"] # set to "eduvac" if you want to restrict usage to only users tagged "eduvac" in users_config.yaml
  avatar_url: ../public/eduvac.png
  description: Educate yourself in your own personal documents via guided learning from Eduvac, the ever patient teacher bot. Use search filters to examine available syllabus or upload your own documents to get started.
  upload:   # to accept uploads of private documents to a bucket
    mime_types:
      - all
    buckets:
      all: your-bucket
  buckets:
    raw: your-bucket
  docstore: # this needs to be valid to have document storage
    - alloydb-docstore:
        type: alloydb
  alloydb_config:
    project_id: your-projectid
    region: europe-west1
    cluster: your-cluster
    instance: primary-instance-1
sample_vector:
  llm: azure
  model: gpt-4-turbo-1106-preview
  agent: langserve
  display_name: Sample vector for tests
  avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
  description: An Azure OpenAI example
  memory:
    - lancedb-vectorstore:
        vectorstore: lancedb
        provider: LanceDB 
  embedder:
    llm: azure
  azure:
    azure_openai_endpoint: https://openai-central-se-amass.openai.azure.com/
    openai_api_version: 2024-02-01
    embed_model: text-embedding-ada-002 # or text-embedding-3-large
```

## cloud_run_urls.json

This is an auto-generated file oon Multivac that lets the VACs know where are other endpoints.  You can also specify this manually if you have deployed to localhost or otherwise.

```json
{
    "agents":"https://agents-xxxx.a.run.app",
    "chunker":"https://chunker-xxxx.a.run.app",
    "embedder":"https://embedder-xxxx.a.run.app",
    "litellm":"https://litellm-xxxx.a.run.app",
    "slack":"https://slack-xxxx.a.run.app",
    "unstructured":"https://unstructured-xxxx.a.run.app"
}
```

## agent_config.yaml

Once the URL is found via the `cloud_run_urls.json` above, this configuration file sets up standard endpoints.

```yaml
# this config file controls the behaviour of agent-types such as langserve, controlling what endpoints are used
default:
  stream: "{stem}/stream"
  invoke: "{stem}/invoke"

langserve:
  stream: "{stem}/{vector_name}/stream"
  invoke: "{stem}/{vector_name}/invoke"
  input_schema: "{stem}/{vector_name}/input_schema"
  output_schema: "{stem}/{vector_name}/output_schema"
  config_schema: "{stem}/{vector_name}/config_schema"
  batch: "{stem}/{vector_name}/batch"
  stream_log: "{stem}/{vector_name}/stream_log"

edmonbrain:
  stream: "{stem}/qna/streaming/{vector_name}"
  invoke: "{stem}/qna/{vector_name}"

openinterpreter:
  stream: "{stem}/qna/streaming/{vector_name}"
  invoke: "{stem}/qna/{vector_name}"

crewai:
  stream: "{stem}/qna/streaming/{vector_name}"
  invoke: "{stem}/qna/{vector_name}"
```

