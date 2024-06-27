# Config files

A main aim for the `sunholo` library is to have as much of the functionality needed for GenAI apps available via configuration files, rather than within the code.

This allows you to set up new instances of GenAI apps quickly, and experiment with new models, vectorstores and other features.  

There are various config files available that control different features such as VAC behaviour and user access.  This is very much still a work in progress so the format may change in the future.

## Calling config files

Use the config functions within [`sunholo.utils`](sunholo/utils/config) to use the config files within your GenAI application.  The most often used config is `vacConfig` below, which is called like this:

```python
from sunholo.utils import load_config_key

vector_name = 'pirate_speak'
llm = load_config_key('llm', vector_name, kind='vacConfig')
# 'openai'
agent = load_config_key('agent', vector_name, kind='vacConfig')
# 'langserve'

vector_name = 'eduvac'
llm = load_config_key('llm', vector_name, kind='vacConfig')
# 'anthropic'
agent = load_config_key('agent', vector_name, kind='vacConfig')
# 'eduvac'
```

You can call your config files anything, just make sure they are in the `config/` folder relative to your working directory, or as configured via the `_CONFIG_FOLDER` environment variable.

## sunholo CLI

A CLI command is included to more easily inspect and validate configurations.

```bash
sunholo list-configs
#'## Config kind: promptConfig'
#{'apiVersion': 'v1',
# 'kind': 'promptConfig',
# 'prompts': {'eduvac': {'chat_summary': 'Summarise the conversation below:\n'
#                                        '# Chat History\n'
#                                        '{chat_history}\n'
#                                        '# End Chat History\n'
#                                        'If in the chat history is a lesson '
# ...                

sunholo list-configs --kind 'vacConfig'
## Config kind: vacConfig
#{'apiVersion': 'v1',
# 'kind': 'vacConfig',
# 'vac': {'codey': {'agent': 'edmonbrain_rag',
# ...

sunholo list-configs --kind=vacConfig --vac=edmonbrain           
## Config kind: vacConfig
#{'edmonbrain': {'agent': 'edmonbrain',
#                'avatar_url': 'https://avatars.githubusercontent.com/u/3155884?s=48&v=4',
#                'description': 'This is the original '
#                               '[Edmonbrain](https://code.markedmondson.me/running-llms-on-gcp/) '
#                               'implementation that uses RAG to answer '
#                               'questions based on data you send in via its '
# ...

# add the --validate flag to check the configuration against a schema
sunholo list-configs --kind=vacConfig --vac=edmonbrain --validate           
## Config kind: vacConfig
#{'edmonbrain': {'agent': 'edmonbrain',
#                'avatar_url': 'https://avatars.githubusercontent.com/u/3155884?s=48&v=4',
#                'description': 'This is the original '
#                               '[Edmonbrain](https://code.markedmondson.me/running-llms-on-gcp/) '
#                               'implementation that uses RAG to answer '
#                               'questions based on data you send in via its '
# ...
#Validating configuration for kind: vacConfig
#Validating vacConfig for edmonbrain
#OK: Validated schema
```

You can use the `--validate` flag in CI/CD to check the configuration each commit, for example in Cloud Build:

```yaml
...
  - name: 'python:3.9'
    id: validate config
    entrypoint: 'bash'
    waitFor: ["-"]
    args:
    - '-c'
    - |
      pip install --no-cache sunholo
      sunholo list-configs --validate || exit 1
```

## vacConfig

This is the main day to day configuration file that is used to set LLMs, databases and VAC tags.  An example is shown here:

```yaml
kind: vacConfig
apiVersion: v1
gcp_config: # reached via vac='global'
  project_id: default-gcp-project
  location: europe-west1
  endpoints_base_url: https://endpoints-xxxxx.a.run.app # if using Cloud Endpoints
vac:
  personal_llama:
    llm: vertex  # using google vertex
    model: gemini-1.5-pro-preview-0514 # models within google vertex
    agent: vertex-genai # using VAC created for Vertex
    display_name: Lots of Vertex AI features # for UI to the end user
    code_execution: true # to add code execution abilities
    grounding: # vertex only - add grounding
      google_search: true
    memory: # multiple memory allowed
      - discovery_engine_vertex_ai_search:
          vectorstore: vertex_ai_search # or 'discovery_engine'
      - llamaindex-native:
          vectorstore: llamaindex # only on vertex
          rag_id: 4611686018427387904 # generated via vertex RAG
      - agent_data_store:
          vectorstore: vertexai_agent_builder # only on vertex
          data_store_id: 1231231231231  # generated via vertex
    gcp_config:
      project_id: multivac-internal-dev # default project
      location: us-central1   # default location
    chunker: # control chunking behaviour when sending data to llamaindex
      chunk_size: 1000
      overlap: 200
    pirate_speak:
        llm: openai
        agent: langserve
        #agent_url: you can specify manually your URL endpoint here, or on Multivac it will be populated automatically
        display_name: Pirate Speak
        tags: ["free"] # for user access, matches users_config.yaml
        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
        description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that will repeat back what you say but in a pirate accent.  Ooh argh me hearties!  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.
    eduvac:
        llm: anthropic
        model: claude-3-opus-20240229
        agent: eduvac # needs to match multivac service name
        agent_type: langserve # if you are using langserve instance for each VAC, you can specify its derived from langserve
        display_name: Edu-VAC
        tags: ["free"] # set to "eduvac" if you want to restrict usage to only users tagged "eduvac" in users_config.yaml
        avatar_url: ../public/eduvac.png
        description: Educate yourself in your own personal documents via guided learning from Eduvac, the ever patient teacher bot. Use search filters to examine available syllabus or upload your own documents to get started.
        upload:   # to accept uploads of private documents to a bucket
            mime_types: # pick which mime types got to which bucket
            - all
            buckets:
                all: your-bucket
        buckets: # pick which bucket takes default uploads
            raw: your-bucket
        docstore: # this needs to be valid to have document storage
            - alloydb-docstore: # you can have multiple doc stores
                type: alloydb
        alloydb_config: # example if using alloydb as your doc or vectorstore
            project_id: your-projectid
            region: europe-west1
            cluster: your-cluster
            instance: primary-instance-1
    csv_agent:
        llm: openai
        agent: langserve
        #agent_url: you can specify manually your URL endpoint here, or on Multivac it will be populated automatically
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
        memory: # you can have multiple destinations for your embedding pipelines
            - lancedb-vectorstore:
                vectorstore: lancedb
                read_only: true # don't write embeddings to this vectorstore 
    finetuned_model:
        llm: model_garden # an example of a custom model such as Llama3 served by Vertex Model Garden
        agent: langserve
        tags: ["clientA"]
        gcp_config: # details of the Model Garden endpoint
            project_id: model_garden_project
            endpoint_id: 12345678
            location: europe-west1
    image_talk:
        llm: vertex
        model: gemini-1.0-pro-vision
        agent: langserve
        upload: # example of accepting uploads
            mime_types:
            - image
        display_name: Talk to Images
        tags: ["free"]
        avatar_url: https://avatars.githubusercontent.com/u/1342004?s=200&v=4
        description: A picture is worth a thousand words, so upload your picture and ask your question to the Gemini Pro Vision model.  Images are remembered for your conversation until you upload another.  This offers powerful applications, which you can get a feel for via the [Gemini Pro Vision docs](https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal/design-multimodal-prompts) 
    sample_vector:
        llm: azure # using Azure OpenAI endpoints
        model: gpt-4-turbo-1106-preview
        agent: langserve
        display_name: Sample vector for tests
        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
        description: An Azure OpenAI example
        memory: # you can have multiple vectorstore destinations
            - lancedb-vectorstore:
                vectorstore: lancedb
        embedder:
            llm: azure
        azure: # your azure details
            azure_openai_endpoint: https://openai-central-blah.openai.azure.com/
            openai_api_version: 2024-02-01
            embed_model: text-embedding-ada-002 # or text-embedding-3-large
    edmonbrain:
      llm: openai
      agent: edmonbrain
      display_name: Edmonbrain
      avatar_url: https://avatars.githubusercontent.com/u/3155884?s=48&v=4
      description: This is the original [Edmonbrain](https://code.markedmondson.me/running-llms-on-gcp/) implementation that uses RAG to answer questions based on data you send in via its `!help` commands and learns from previous chat history.  It dreams each night that can also be used in its memory.
      model: gpt-4o
      user_special_cmds: # allows commands that execute before a call to the model for user interaction
        - "!saveurl"
        - "!savethread"
      memory_k: 10 # how many memories will be returned in total after relevancy compression
      memory:
        - personal-vectorstore:
            vectorstore: lancedb
            k: 10 #  how many candidate memory will be returned from this vectorstore
        - eduvac-vectorstore:
            vector_name: eduvac
            read_only: true # can only read, not write embeddings
            vectorstore: lancedb
            k: 3 #  how many candidate memory will be returned from this vectorstore
```

## agentConfig

This configuration file sets up standard endpoints for each type of agent, corresponding to a VAC running.  It is also used to help create a [Swagger specification](https://swagger.io/) for use when deploy to service such as Cloud Endpoints.

```yaml
# this config file controls the behaviour of agent-types such as langserve, controlling what endpoints are used
kind: agentConfig
apiVersion: v2
agents:
  default:
    #post-noauth:
      # add post endpoints that do not need authentication
    #get-auth:
      # add get endpoints that do need authentication
    post:
      stream: "{stem}/vac/streaming/{vector_name}"
      invoke: "{stem}/vac/{vector_name}"
      openai: "{stem}/openai/v1/chat/completions"
      openai-vac: "{stem}/openai/v1/chat/completions/{vector_name}"
    get:
      home: "{stem}"
      health: "{stem}/health"
    response:
      invoke:
        '200':
          description: Successful invocation response
          schema:
            type: object
            properties:
              answer:
                type: string
              source_documents:
                type: array
                items:
                  type: object
                  properties:
                    page_content:
                      type: string
                    metadata:
                      type: string
      stream:
        '200':
          description: Successful stream response
          schema:
            type: string
      openai:
        '200':
          description: Successful OpenAI response
          schema:
            type: object
            properties:
              id:
                type: string
              object:
                type: string
              created:
                type: string
              model:
                type: string
              system_fingerprint:
                type: string
              choices:
                type: array
                items:
                  type: object
                  properties:
                    index:
                      type: integer
                    delta:
                      type: object
                      properties:
                        content:
                          type: string
                    logprobs:
                      type: string
                    finish_reason:
                      type: string
              usage:
                type: object
                properties:
                  prompt_tokens:
                    type: integer
                  completion_tokens:
                    type: integer
                  total_tokens:
                    type: integer
      openai-vac:
        '200':
          description: Successful OpenAI VAC response
          schema:
            type: object
            properties:
              id:
                type: string
              object:
                type: string
              created:
                type: string
              model:
                type: string
              system_fingerprint:
                type: string
              choices:
                type: array
                items:
                  type: object
                  properties:
                    index:
                      type: integer
                    message:
                      type: object
                      properties:
                        role:
                          type: string
                        content:
                          type: string
                    logprobs:
                      type: string
                    finish_reason:
                      type: string
              usage:
                type: object
                properties:
                  prompt_tokens:
                    type: integer
                  completion_tokens:
                    type: integer
                  total_tokens:
                    type: integer
      home:
        '200':
          description: OK
          schema:
            type: string
      health:
        '200':
          description: A healthy response
          schema:
            type: object
            properties:
              status:
                type: string
        '500':
          description: Unhealthy response
          schema:
            type: string

  eduvac:
    get:
      docs: "{stem}/docs"
    get-auth:
      playground: "{stem}/{vector_name}/playground"
    post:
      stream: "{stem}/{vector_name}/stream"
      invoke: "{stem}/{vector_name}/invoke"
      input_schema: "{stem}/{vector_name}/input_schema"
      output_schema: "{stem}/{vector_name}/output_schema"
      config_schema: "{stem}/{vector_name}/config_schema"
      batch: "{stem}/{vector_name}/batch"
      stream_log: "{stem}/{vector_name}/stream_log"

  langserve:
    get:
      docs: "{stem}/docs"
      playground: "{stem}/{vector_name}/playground"
    get-auth:
      playground: "{stem}/{vector_name}/playground"    
    post-noauth:
      # add post endpoints that do not need authentication
      output_schema: "{stem}/{vector_name}/output_schema"
    post:
      stream: "{stem}/{vector_name}/stream"
      invoke: "{stem}/{vector_name}/invoke"
      input_schema: "{stem}/{vector_name}/input_schema"
      config_schema: "{stem}/{vector_name}/config_schema"
      batch: "{stem}/{vector_name}/batch"
      stream_log: "{stem}/{vector_name}/stream_log"

```

## userConfig

This lets you do user authentication by matching the tags within `llm_config.yaml` with user email domains

```yaml
kind: userConfig
apiVersion: v1
user_groups:
  - name: "admin"
    domain: "sunholo.com"
    role: "ADMIN"
    tags:
      - "admin_user"

  - name: "eduvac"
    emails:
      - "multivac@sunholo.com"
    role: "eduvac"
    tags:
      - "eduvac"

  # Example of another firm using both domain and specific emails
  - name: "another_firm"
    domain: "anotherfirm.com"
    emails:
      - "specialcase@anotherfirm.com"
    role: "partner"
    tags:
      - "partner"

default_user:
  role: "USER"
  tags:
    - "user"

```

## promptConfig

This file contains various prompts for a vector_name of a VAC.  It is preferred that the native [Langfuse prompt library](https://langfuse.sunholo.com) is used, but this yaml file is a backup if its not available via Langfuse.

```yaml
kind: promptConfig
apiVersion: v1
prompts:
  eduvac:
    intro: |
      You are an expert teacher versed with the latest techniques to enhance learning with your students.
      Todays date is {the_date}
      Please create an assignment for the student that will demonstrate their understanding of the text. 
    template: |
      Answer the question below with the help of the following context.  
      # Context
      {metadata}
      # End Context

      This is the conversation so far
      # Chat Summary
      ...{chat_summary}
      # Chat History
      ...{chat_history}
      # End of Chat History

      If you have made an earlier plan in your chat history, 
      briefly restate it and update where you are in that plan to make sure to 
      keep yourself on track and to not forget the original purpose of your answers.

      Question: {question}
      Your Answer:
    chat_summary: |
      Summarise the conversation below:
      # Chat History
      {chat_history}
      # End Chat History
      Your Summary of the chat history above:
    summarise_known_question: |
      You are an teacher assistant to a student and teacher who has has this input from the student:
      {question}

      # Chat history (teacher and student)
      {chat_history}
      # End Chat History

      # Context (what the student is learning)
      {context}
      # end context
      Assess if the student has completed the latest tasks set by the teacher, 
      with recommendations on what the student and teacher should do next. 


      Your Summary:
```
