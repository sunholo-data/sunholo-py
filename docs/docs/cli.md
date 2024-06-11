# Sunholo CLI

A CLI is installed via `sunholo[cli]`

```bash
$> pip install sunholo[cli]

$> sunholo --help
╭───────────────────────────────────────────── Sunholo GenAIOps Assistant CLI ─────────────────────────────────────────────╮
│ Welcome to Sunholo Command Line Interface, your assistant to deploy GenAI Virtual Agent Computers (VACs) to Multivac or  │
│ your own Cloud.                                                                                                          │
╰─────────────────────────────────────── Documentation at https://dev.sunholo.com/ ────────────────────────────────────────╯
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
usage: sunholo [-h] [--debug] [--project PROJECT] [--region REGION]
               {deploy,list-configs,init,merge-text,proxy,vac,embed} ...

sunholo CLI tool for deploying GenAI VACs

optional arguments:
  -h, --help            Show this help message and exit
  --debug               Enable debug output
  --project PROJECT     GCP project to list Cloud Run services from.
  --region REGION       Region to list Cloud Run services from.

commands:
  Valid commands

  {deploy,list-configs,init,merge-text,proxy,vac,embed}
                        Commands
    deploy              Triggers a deployment of a VAC.
    list-configs        Lists all configuration files and their details
    init                Initializes a new Multivac project.
    merge-text          Merge text files from a source folder into a single output file.
    proxy               Set up or stop a proxy to the VAC Cloud Run services
    vac                 Interact with deployed VAC services.
    embed               Send data for embedding to a VAC vector store
```

## sunholo list-configs

This helps examine and validate the YAML configuration files that are central to the sunholo library.

```bash
$> sunholo list-configs -h
usage: sunholo list-configs [-h] [--kind KIND] [--vac VAC] [--validate]

optional arguments:
  -h, --help   show this help message and exit
  --kind KIND  Filter configurations by kind e.g. `--kind=vacConfig`
  --vac VAC    Filter configurations by VAC name e.g. `--vac=edmonbrain`
  --validate   Validate the configuration files.
```

### Examples

```bash
$> sunholo list-configs
#'## Config kind: promptConfig'
#{'apiVersion': 'v1',
# 'kind': 'promptConfig',
# 'prompts': {'eduvac': {'chat_summary': 'Summarise the conversation below:\n'
#                                        '# Chat History\n'
#                                        '{chat_history}\n'
#                                        '# End Chat History\n'
#                                        'If in the chat history is a lesson '
# ...                

$> sunholo list-configs --kind 'vacConfig'
## Config kind: vacConfig
#{'apiVersion': 'v1',
# 'kind': 'vacConfig',
# 'vac': {'codey': {'agent': 'edmonbrain_rag',
# ...

$> sunholo list-configs --kind=vacConfig --vac=edmonbrain           
## Config kind: vacConfig
#{'edmonbrain': {'agent': 'edmonbrain',
#                'avatar_url': 'https://avatars.githubusercontent.com/u/3155884?s=48&v=4',
#                'description': 'This is the original '
#                               '[Edmonbrain](https://code.markedmondson.me/running-llms-on-gcp/) '
#                               'implementation that uses RAG to answer '
#                               'questions based on data you send in via its '
# ...

# add the --validate flag to check the configuration against a schema
$> sunholo list-configs --kind=vacConfig --vac=edmonbrain --validate           
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
      pip install --no-cache sunholo[cli]
      sunholo list-configs --validate || exit 1
      sunholo list-configs --kind=vacConfig --vac=${_SERVICE_NAME} --validate || exit 1
```

## sunholo merge-text

Useful to turn a folder into one text file for large context windows.

```bash
$> sunholo merge-text -h 
usage: sunholo merge-text [-h] [--gitignore GITIGNORE] [--output_tree] source_folder output_file

positional arguments:
  source_folder         Folder containing the text files.
  output_file           Output file to write the merged text.

optional arguments:
  -h, --help            show this help message and exit
  --gitignore GITIGNORE
                        Path to .gitignore file to exclude patterns.
  --output_tree         Set to output the file tree in the console after merging
```

## sunholo proxy

When you have Cloud Run VACs running in the cloud, you can proxy them to your local session to help with debugging and local applications.  Since by default most VACs are behind a VPC, they usually can not be called via public URLs, aside if they are web apps or chat bot clients.

You can set the project_id and region via the global `--project_id` and `--region` flags.  But it is recommended to also use the `vacConfig` file to set up the `gcp_config` section for easier use.

The `sunholo proxy` command will let you proxy any Cloud Run service via [`gcloud run services proxy`](https://cloud.google.com/sdk/gcloud/reference/run/services/proxy) - you will need to be authenticated with `gcloud` for the services you want to use.

Example yaml:

```yaml
kind: vacConfig
apiVersion: v1
gcp_config:
  project_id: multivac-internal-dev
  location: europe-west1
vac:
  #... you vacs configs ...
```

```bash
$> sunholo proxy --help

usage: sunholo proxy [-h] {start,stop,list,stop-all,list-vacs} ...

positional arguments:
  {start,stop,list,stop-all,list-vacs}
    start               Start the proxy to the Cloud Run service.
    stop                Stop the proxy to the Cloud Run service.
    list                List all running proxies.
    stop-all            Stop all running proxies.

optional arguments:
  -h, --help            show this help message and exit
```

### Examples


```bash
$> sunholo proxy list
                    VAC Proxies                     
┏━━━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ VAC       ┃ Port ┃ PID   ┃ URL                   ┃
┡━━━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ langserve │ 8080 │ 28213 │ http://127.0.0.1:8080 │
└───────────┴──────┴───────┴───────────────────────┘

$> sunholo proxy start edmonbrain
Proxy for edmonbrain setup complete on port 8081
                     VAC Proxies                     
┏━━━━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ VAC        ┃ Port ┃ PID   ┃ URL                   ┃
┡━━━━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ langserve  │ 8080 │ 28213 │ http://127.0.0.1:8080 │
│ edmonbrain │ 8081 │ 28353 │ http://127.0.0.1:8081 │
└────────────┴──────┴───────┴───────────────────────┘

$> sunholo proxy stop edmonbrain
Proxy for edmonbrain stopped.
                    VAC Proxies                     
┏━━━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ VAC       ┃ Port ┃ PID   ┃ URL                   ┃
┡━━━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ langserve │ 8080 │ 28213 │ http://127.0.0.1:8080 │
└───────────┴──────┴───────┴───────────────────────┘

$> sunholo proxy stop-all
Proxy for langserve stopped.
No proxies currently running.
```

### Local testing

If you have a local VAC running via a Flask or FastAPI app.py that will be deployed to Cloud Run or similar, then you can proxy that local VAC instead of the cloud version by using the `--local` flags and specifying the VAC local folder:

```bash
$> sunholo proxy start edmonbrain --local --app-type flask --app-folder . --log-file
                         VAC Proxies - `sunholo proxy list`                          
                              VAC Proxies - `sunholo proxy list`                               
┏━━━━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ VAC        ┃ Port ┃ PID   ┃ URL                   ┃ Local            ┃ Logs                 ┃
┡━━━━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ edmonbrain │ 8080 │ 99669 │ http://127.0.0.1:8080 │ ./app.py - flask │ ./edmonbrain_log.txt │
└────────────┴──────┴───────┴───────────────────────┴──────────────────┴──────────────────────┘
```

This makes local testing easier before you deploy via Cloud Build or similar.

When using `sunholo vac` below, it will start/stop a Cloud proxy for you if it is not running already.  It will not start/stop a locally running app.

## sunholo vac

This allows you to interact with the Multivac cloud VACs with an interactive or headless client in your terminal, rather than the Web App or Chat bots.  It allows for quick debugging and opens up use cases for GenAI scripts calling VACs.

It requires a `vacConfig` setup with details of the VACs you are calling e.g.

```yaml
kind: vacConfig
apiVersion: v1
gcp_config:
  project_id: multivac-internal-dev
  location: europe-west1
vac:
  multivac_docs:
    llm: vertex
    model: gemini-1.0-pro
    agent: langserve
    display_name: Multivac
    tags: ["free"]
    avatar_url: https://avatars.githubusercontent.com/u/147247777?s=200&v=4
    description: What is Multivac? Talk to us about our Electric Dreams and hopes for the future. Explain to me below in the chat box what your business use case is and I will try to help you. If you don't have a use case right now, you can start with "What is Sunholo Multivac? or select another VAC from the drop down."
    memory:
      - lancedb-vectorstore:
          vectorstore: lancedb
```

### Usage

```bash
$> sunholo vac --help
usage: sunholo vac [-h] [--url_override URL_OVERRIDE] [--no-proxy] {list,get-url,chat,invoke} ...

positional arguments:
  {list,get-url,chat,invoke}
                        VAC subcommands
    list                List all VAC services.
    get-url             Get the URL of a specific VAC service.
    chat                Interact with a VAC service.
    invoke              Invoke a VAC service directly with custom data.

optional arguments:
  -h, --help            show this help message and exit
  --url_override URL_OVERRIDE
                        Override the VAC service URL.
  --no-proxy            Do not use the proxy and connect directly to the VAC service.
```

### Authentication via `roles/run.invoker`

Your local `gcloud` user needs to have IAM access of `roles/run.invoker` to the VAC service to be able to call it, else you will get the error:

> There was an error processing your request. Please try again later. 500 Server Error: 
> Internal Server Error for url: http://127.0.0.1:8080/vac/streaming/edmonbrain`


### Examples

List all the VACs available to your account for the project defined.

```bash
$> sunholo vac list
                                       VAC Cloud Run Services                                        
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━┓
┃ Service Name     ┃ Region       ┃ URL                                            ┃ Proxied ┃ Port ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━┩
│ chunker          │ europe-west1 │ https://chunker-xxxxxxxxxxxxx.a.run.app        │ No      │ -    │
│ crewai           │ europe-west1 │ https://crewai-xxxxxxxxxxxxx.a.run.app         │ No      │ -    │
│ discord-server   │ europe-west1 │ https://discord-server-xxxxxxxxxxxxx.a.run.app │ No      │ -    │
│ dreamer          │ europe-west1 │ https://dreamer-xxxxxxxxxxxxx.a.run.app        │ No      │ -    │
│ edmonbrain       │ europe-west1 │ https://edmonbrain-xxxxxxxxxxxxx.a.run.app     │ No      │ -    │
│ edmonbrain-agent │ europe-west1 │ https://edmonbrain-agent-xxxxxxxxxxxxx.a.run.… │ No      │ -    │
│ eduvac           │ europe-west1 │ https://eduvac-xxxxxxxxxxxxx.a.run.app         │ No      │ -    │
│ embedder         │ europe-west1 │ https://embedder-xxxxxxxxxxxxx.a.run.app       │ No      │ -    │
│ image-talk       │ europe-west1 │ https://image-talk-xxxxxxxxxxxxx.a.run.app     │ No      │ -    │
│ langfuse         │ europe-west1 │ https://langfuse-xxxxxxxxxxxxx.a.run.app       │ No      │ -    │
│ langserve        │ europe-west1 │ https://langserve-xxxxxxxxxxxxx.a.run.app      │ Yes     │ -    │
│ litellm          │ europe-west1 │ https://litellm-xxxxxxxxxxxxx.a.run.app        │ No      │ -    │
│ openinterpreter  │ europe-west1 │ https://openinterpreter-xxxxxxxxxxxxx.a.run.a… │ No      │ -    │
│ our-new-energy   │ europe-west1 │ https://our-new-energy-xxxxxxxxxxxxx.a.run.app │ No      │ -    │
│ promptfoo        │ europe-west1 │ https://promptfoo-xxxxxxxxxxxxx.a.run.app      │ No      │ -    │
│ ragapp           │ europe-west1 │ https://ragapp-xxxxxxxxxxxxx.a.run.app         │ No      │ -    │
│ rags             │ europe-west1 │ https://rags-xxxxxxxxxxxxx.a.run.app           │ No      │ -    │
│ reactapp         │ europe-west1 │ https://reactapp-xxxxxxxxxxxxx.a.run.app       │ No      │ -    │
│ slack            │ europe-west1 │ https://slack-xxxxxxxxxxxxx.a.run.app          │ No      │ -    │
│ sunholo-website  │ europe-west1 │ https://sunholo-website-xxxxxxxxxxxxx.a.run.a… │ No      │ -    │
│ unstructured     │ europe-west1 │ https://unstructured-xxxxxxxxxxxxx.a.run.app   │ No      │ -    │
│ vertex-genai     │ europe-west1 │ https://vertex-genai-xxxxxxxxxxxxx.a.run.app   │ No      │ -    │
│ webapp           │ europe-west1 │ https://webapp-xxxxxxxxxxxxx.a.run.app         │ No      │ -    │
└──────────────────┴──────────────┴────────────────────────────────────────────────┴─────────┴──────┘
```

Get the URL of a specific VAC

```bash
$> sunholo vac get-url edmonbrain
https://edmonbrain-xxxxxxxx.a.run.app
```

Chat with a VAC from the command line.  To exit a chat, use `exit`

```bash
$> sunholo vac chat --help
usage: sunholo vac chat [-h] [--headless] [--chat_history CHAT_HISTORY] [--no_proxy] vac_name [user_input]

positional arguments:
  vac_name              Name of the VAC service.
  user_input            User input for the VAC service when in headless mode.

optional arguments:
  -h, --help            show this help message and exit
  --headless            Run in headless mode.
  --chat_history CHAT_HISTORY
                        Chat history for headless mode (as JSON string).
  --no_proxy            Do not use the proxy and connect directly to the VAC service.

$> sunholo vac chat multivac_docs
No proxy found running for service: langserve required for multivac_docs - attempting to connect
Proxy for langserve setup complete on port 8081
                     VAC Proxies                     
┏━━━━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ VAC        ┃ Port ┃ PID   ┃ URL                   ┃
┡━━━━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ langserve  │ 8080 │ 28213 │ http://127.0.0.1:8080 │
│ edmonbrain │ 8081 │ 28353 │ http://127.0.0.1:8081 │
└────────────┴──────┴───────┴───────────────────────┘

╭──────────────────────────────────────────── Multivac ─────────────────────────────────────────────╮
│ What is Multivac? Talk to us about our Electric Dreams and hopes for the future. Explain to me    │
│ below in the chat box what your business use case is and I will try to help you. If you don't     │
│ have a use case right now, you can start with "What is Sunholo Multivac? or select another VAC    │
│ from the drop down."                                                                              │
╰───────────────────────── http://127.0.0.1:8080/multivac_docs/playground/ ─────────────────────────╯
You: 
```

Interact via the terminal.  This will call the VAC online via the proxy.  The proxy URL is also displayed to help debug via tools such as `curl`:

```bash
╭──────────────────────────────────────────── Multivac ─────────────────────────────────────────────╮
│ What is Multivac? Talk to us about our Electric Dreams and hopes for the future. Explain to me    │
│ below in the chat box what your business use case is and I will try to help you. If you don't     │
│ have a use case right now, you can start with "What is Sunholo Multivac? or select another VAC    │
│ from the drop down."                                                                              │
╰───────────────────────── http://127.0.0.1:8080/multivac_docs/playground/ ─────────────────────────╯
You: what is sunholo multivac?
✹ Thinking...
```

Output:

```bash
You: what is sunholo multivac?
multivac_docs: ## What is Sunholo Multivac?

Sunholo Multivac is a platform designed to simplify the deployment and use of GenAI applications within your...
...

You: exit
Exiting chat session.
```

### Headless mode

With headless mode, you just get the answer streamed to terminal.  Ask your question quoted in the next positional argument:

```sh
$> sunholo vac chat multivac_docs "What is Sunholo Multivac?" --headless
## What is Sunholo Multivac?

Sunholo Multivac is a platform designed to simplify the deployment and use of GenAI applications within your... 
...
```

This output can be piped into other shell commands e.g. to write to a file:

```bash
$> sunholo vac chat multivac_docs "What is Sunholo Multivac?" --headless > response.txt
$> cat response.txt
## What is Sunholo Multivac?

Sunholo Multivac is a platform designed to simplify the deployment and use of GenAI applications within your... 
...
```

### No Proxy

When using with public endpoints such as the webapp, or within Multivac VPC, no proxy is needed.  This allows you to use within CI/CD to run integration tests of your VACs after deployment, such as within Cloud Build:

```yaml
...
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: 'bash'
    dir: ${_BUILD_FOLDER}
    id: check VAC working
    args:
    - '-c'
    - |
        apt-get update && apt-get install -y python3-pip
        pip3 install --no-cache-dir sunholo[cli]
        sunholo vac --no-proxy chat edmonbrain 'hello' --headless || exit 1
...
```

### sunholo vac invoke

This command is equivalent to `curl` commands you may use otherwise, but helps resolve the URL of the VAC service.

```bash
$> sunholo vac invoke --help
usage: sunholo vac invoke [-h] [--is-file] vac_name data

positional arguments:
  vac_name    Name of the VAC service.
  data        Data to send to the VAC service (as JSON string).

optional arguments:
  -h, --help  show this help message and exit
  --is-file   Indicate if the data argument is a file path
```

For example, you may have a VAC service not on Google Cloud Platform, but upon Azure.  Deploying the Docker service to Azure container apps, you can still invoke the VAC service alongside the GCP proxy services by overriding the URL:

```bash
$> export FLASK_URL=https://chunker.your-azure-id.northeurope.azurecontainerapps.io/
$> sunholo vac --url_override ${FLASK_URL}/pubsub_to_store invoke chunker '{
          "message": {
            "data": "aHR0cHM6Ly93d3cuYW1hc3MudGVjaC8=", # https://amass.tech 
            "attributes": {
              "namespace": "sample_vector",
              "return_chunks": true
            }
          }
        }'
```
```json
{
    'chunks': [
        {
            'metadata': {
                ...
            },
            'page_content': 'Supercharge Your R&D Productivity\nSynthesize scientific research across millions of internal and external data sources...
        }
    ],
    'status': 'Success'
}
```

## sunholo embed

This lets you submit content to a VAC's vector store from the command line, instead of say the bucket or pub/sub embedding pipeline.

The VAC you are sending to requires to have its `memory` configuration setup for the vector store you are using eg. the example below has the `memory.lancedb-vectorstore` set up determining where chunks for that VAC are sent.  You can have multiple memory destinations, see [`config`](config) for more details.

```yaml
kind: vacConfig
apiVersion: v1
gcp_config:
  project_id: multivac-internal-dev
  location: europe-west1
vac:
  multivac_docs:
    llm: vertex
    model: gemini-1.0-pro
    agent: langserve
    memory:
      - lancedb-vectorstore:
          vectorstore: lancedb
```

### sunholo embed examples

The `sunholo embed` command lets you use your deployed chunker and embedder VAC system services, or if you have deployed your own you can supply your own URLs via `--embed_override` and/or `--chunk_override`.  By default the VACs will be launched locally via the Proxy using your `gcloud` credentials, but if you are within the Multivac VPC then use `--no-proxy` to send them directly to the VACs.

The chunker has the same properties as the Multivac Embedder VAC (it is the same) so you can trigger file imports by supplying a Cloud Storage bucket `gs://` URI; or imports via Google drive / git or embed URLs via `http://` URIs.

By default when using Multivac Cloud, it will send the content you want to embed to the chunker, then the embedder within the Cloud (via PubSub).  However, if you want to do this locally, use `--local-chunks` to return the chunks to your local session, and pass those chunks to the embedding endpoint.

```bash
$> sunholo embed --help
usage: sunholo embed [-h] [--embed-override EMBED_OVERRIDE] [--chunk-override CHUNK_OVERRIDE] [--no-proxy] [-m METADATA]
                     [--local-chunks] [--is-file] [--only-chunk]
                     vac_name data

positional arguments:
  vac_name              VAC service to embed the data for
  data                  String content to send for embedding

optional arguments:
  -h, --help            show this help message and exit
  --embed-override EMBED_OVERRIDE
                        Override the embed VAC service URL.
  --chunk-override CHUNK_OVERRIDE
                        Override the chunk VAC service URL.
  --no-proxy            Do not use the proxy and connect directly to the VAC service.
  -m METADATA, --metadata METADATA
                        Metadata to send with the embedding (as JSON string).
  --local-chunks        Whether to process chunks to embed locally, or via the cloud.
  --is-file             Indicate if the data argument is a file path
  --only-chunk          Whether to only parse the document and return the chunks locally, with no embedding
```

### Examples

```bash
# send a URL for parsing and embedding within the edmonbrain VAC vector store
$> sunholo embed edmonbrain "https://www.amass.tech/"
──────────────────────────────────────────────── Sending data for chunking ─────────────────────────────────────────────────
{
    'chunks': [
        {
            'metadata': {
                ...
            },
            'page_content': 'Supercharge Your R&D Productivity\nSynthesize scientific research across millions of internal 
and external data sources\nLet me try\nPDF\nThe Role of ...etc...'
        }
    ],
    'status': 'success'
}
─ Chunks sent for processing in cloud: {'chunks': [{'metadata': {'category':
```

Send a URL for parsing and embedding within the edmonbrain VAC vector store

```
$> sunholo embed edmonbrain "https://www.amass.tech/" --local-chunks
..chunking as above with additional local processing of embedding..
──────────────────────────────────────────────── Processing chunks locally ─────────────────────────────────────────────────
Working on chunk {'category': 'Title', 'category_depth': 0, 'chunk_number': 0, 'doc_id': 
'7a45e7ec-1f25-5d09-9372-b8439e6769dd', 'eventTime': '2024-06-05T10:54:21Z', 'filetype': 'text/html', 'languages': ['eng'], 
'link_start_indexes': [0], 'link_texts': ['Contact'], 'link_urls': ['./contact'], 'namespace': 'edmonbrain', 
'return_chunks': 'true', 'source': 'https://www.amass.tech/', 'type': 'url_load', 'url': 'https://www.amass.tech/', 
'vector_name': 'edmonbrain'}
Sending chunk length 3389 to embedder
Embedding [1] chunks ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0% -:--:--
...
Embedding [1] chunks ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
─────────────────────────────────────────────── Embedding pipeline finished ────────────────────────────────────────────────
```


This example is using your own URLs from your own Multivac deployments

```bash
$> export CHUNK_URL=https://chunker.your-chunker-url.com
$> export EMBED_URL=https://embedder.your-embedder-url.com
$> sunholo embed edmonbrain "https://www.amass.tech/" --local-chunks --embed-override=$EMBED_URL --chunk-override=$CHUNK_URL

```

You can process local files for uploading by passing the `--is-file` flag and setting data to the file location

```bash
$> sunholo embed --local-chunks edmonbrain README.md --is-file
──────────────────────────────────────────────── Sending data for chunking ─────────────────────────────────────────────────
```
```json
{
    'chunks': [
        {
            'metadata': {
                'category': 'NarrativeText',
                'chunk_number': 0,
                'doc_chunk': 40,
                'eventTime': '2024-06-06T12:32:14Z',
                'filename': 'README.md',
                'filetype': 'text/markdown',
                'languages': ['eng'],
                'parent_id': '5e6a0ba0e08fb994774adb94369c1621',
                'parse_total_doc_chars': 2880,
                'parse_total_doc_chunks': 41,
                'return_chunks': True,
                'source': 'sunholo-cli',
                'vector_name': 'edmonbrain'
            },
            'page_content': 'Introduction\nThis is the Sunholo Python project, a comprehensive toolkit for working with 
language models and vector stores on Google Cloud Platform.... ```'
        }
    ],
    'status': 'success'
}
```
```bash
──────────────────────────────────────────────── Processing chunks locally ─────────────────────────────────────────────────
Working on chunk {'category': 'NarrativeText', 'chunk_number': 0, 'doc_chunk': 40, 'eventTime': '2024-06-06T12:32:14Z', 
'filename': 'README.md', 'filetype': 'text/markdown', 'languages': ['eng'], 'parent_id': '5e6a0ba0e08fb994774adb94369c1621',
'parse_total_doc_chars': 2880, 'parse_total_doc_chunks': 41, 'return_chunks': True, 'source': 'sunholo-cli', 'vector_name': 
'edmonbrain'}
Sending chunk length 2905 to embedder
...
Embedding [1] chunks via http://127.0.0.1:8081 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
─────────────────────────────────────────────── Embedding pipeline finished ────────────────────────────────────────────────
```

If you just would like the document parsed and chunked for you to embed yourself locally, you can use the `--only-chunk` flag, and direct them to a file for example via `> chunks.txt`

```bash
$> sunholo embed --local-chunks edmonbrain docs/docs/index.md --is-file --only-chunk > chunks.txt
──────────────────────────────────────────────── Sending data for chunking ─────────────────────────────────────────────────
✷ Sending docs/docs/index.md to chunk via http://127.0.0.1:8080
...

```

