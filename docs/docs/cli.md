# Sunholo CLI

A CLI is installed via `sunholo"[cli]"`

## Install using uv (recommended)

uv is a new python envioronment library that makes it easy to use python tools such as `sunholo`.

First install `uv' if you haven't got it: https://docs.astral.sh/uv/getting-started/installation/

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You can then run the `sunholo` command by installing its  `[cli]` extra

```bash
uvx --from "sunholo[cli]" sunholo
#Installed 35 packages in 71ms
#usage: sunholo [-h] [--debug] [--project PROJECT] [--region REGION] [-v]
#               {deploy,list-configs,init,merge-text,proxy,vac,embed,swagger,vertex,llamaindex,excel-init,tfvars,tts} ...

#sunholo CLI tool for deploying GenAI VACs
#...
```

To install it within `uv`s cache, use the following command:

```bash
uv tool install --from "sunholo[cli]" sunholo 
```

You can then run it like this:

```bash
sunholo
# usage: sunholo [-h] [--debug] [--project PROJECT] [--region REGION] [-v]
#               {deploy,list-configs,init,merge-text,proxy,vac,embed,swagger,vertex,llamaindex,excel-init,tfvars,tts} ...
#
#sunholo CLI tool for deploying GenAI VACs
```

### Upgrades and installing features

```bash
uv tool upgrade sunholo
# install tool with Anthropic MCP
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[anthropic]"
# install tool with Google Text-to-speech
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[tts]"
# install with both text-to-speech and anthropic
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[anthropic,tts]"
# etc...
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[all]"
```

### Install via pip (legacy)

```bash
pip install sunholo"[cli]"
sunholo --help
```

## sunholo list-configs

This helps examine and validate the YAML configuration files that are central to the sunholo library.

![](img/config-list.gif)

```bash
sunholo list-configs -h
usage: sunholo list-configs [-h] [--kind KIND] [--vac VAC] [--validate]

optional arguments:
  -h, --help   show this help message and exit
  --kind KIND  Filter configurations by kind e.g. `--kind=vacConfig`
  --vac VAC    Filter configurations by VAC name e.g. `--vac=edmonbrain`
  --validate   Validate the configuration files.
```

### Examples

```bash
sunholo list-configs               
sunholo list-configs --kind 'vacConfig'
sunholo list-configs --kind=vacConfig --vac=edmonbrain           
sunholo list-configs --kind=vacConfig --vac=edmonbrain --validate           
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

**If you are using a `MULTIVAC_API_KEY` then you do not need to use a proxy - configure your `config.gcp_config.endpoints_url_base` instead.**

> `sunholo proxy` keeps track of which proxies are running via the file : `os.path.join(os.path.expanduser("~"), '.sunholo_proxy_tracker.json')` e.g. your home directory.

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

![](img/sunholo-vac-chat.gif)

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

#### Authentication via `roles/run.invoker`

Your local `gcloud` user needs to have IAM access of `roles/run.invoker` to the VAC service to be able to call it, else you will get the error:

> There was an error processing your request. Please try again later. 500 Server Error: 
> Internal Server Error for url: http://127.0.0.1:8080/vac/streaming/edmonbrain`


### sunholo vac list

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

### sunholo vac get-url

Get the URL of a specific VAC

```bash
$> sunholo vac get-url edmonbrain
https://edmonbrain-xxxxxxxx.a.run.app
```

### sunholo vac chat

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

#### Interacting with files


##### Uploads

You can upload files to a bucket such as images with `!upload` that can be used to talk with for example image models.  The uploaded file will stay in session until you remove it via `!clear_upload`.  The file is uploaded to the configured Google Cloud Storage bucket.

```bash
You: !upload my_image.png
```

#### Local files inserted into prompts

![](img/sunholo-vac-chat-with-files.gif)

You can also examine whats in your local directory if you've forgotten the name via `!ls`, or print out a file tree with `!tree`

```bash
You: !ls
cloudbuild.yaml
README.md
public
package.json
src

You: !tree
[
    'reactapp/',
    '    cloudbuild.yaml',
    '    README.md',
    '    package.json',
    '    public/',
    '        index.html',
    '    src/',
    '        App.css',
    '        index.js',
    '        index.css',
    '        App.js'
]
```

You can upload files that can be parsed as text (code files, markdown, text etc.) via `!read` that will be prefixed to your questions for that session until you issue `!clear_read`:

```bash
You: !read README.md
File content from README.md read into user_input: [46] words
```

This also work with folders - so you can read in all the text/code files from a folder and have it within your prompt for each question (useful for code assistants).  It uses the `sunholo merge-text` functions to read through a folder and merge all availabel files, respecting the `.gitignore` file:

> Be careful to not spend lots of money on tokens by prefixing your prompts with a huge folder worth of text!

```bash
You: !read reactapp
- merging reactapp...
- merging reactapp/public...
- merging reactapp/src...
Contents of the folder 'reactapp' have been merged add added to input.
reactapp/
    .DS_Store
    cloudbuild.yaml
    README.md
    package.json
    public/
        index.html
    src/
        App.css
        index.js
        index.css
        App.js
Total words: [1801] - watch out for high token costs! Use !clear_read to reset
```

An example of how it can be used is below:

```bash
mark@macbook-air application % sunholo vac chat personal_llama
╭──────────────────────────────────── Personal Llama ─────────────────────────────────────╮
│ Gemini with grounding via Google Search and LlamaIndex                                  │
╰─ stream: https://multivac-api.sunholo.com/v1/vertex-genai/vac/streaming/personal_llama ─╯
You: !read react_app
The provided path is neither a file nor a folder. Please check the path and try again.
You: !read reactapp
- merging reactapp...
- merging reactapp/public...
- merging reactapp/src...
Contents of the folder 'reactapp' have been merged add added to input.
reactapp/
    .DS_Store
    cloudbuild.yaml
    README.md
    package.json
    public/
        index.html
    src/
        App.css
        index.js
        index.css
        App.js
Total words: [1801] - watch out for high token costs! Use !clear_read to reset
You: can you summarise what this react app does and provide an improvement to App.js
✹ Thinking... - additional [1801] words added via !read_file contents - issue !clear_read to remove
```

The response:

````bash
personal_llama: I am very certain that I can answer that based on the provided code. 

This React app is a simple chat interface for a Langchain QNA service (Langserve). 

The user can ask a question, and the React app will send the question to the Langserve 
...etc...
````

> TODO: download any artifact files or parse out code examples to edit the file directly

### sunholo vac chat --headless

With headless mode, you just get the answer streamed to terminal.  Ask your question quoted in the next positional argument:

![](img/sunholo-vac-chat-headless.gif)

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

### sunholo vac --no-proxy

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


## sunholo swagger

This creates a swagger file from the `agentConfig` and `vacConfig` files for use with the agent APIs.  It was initially generated for the Multivac [Cloud Endpoints](https://cloud.google.com/endpoints) integration and is useful for setting up micro-services and API gateways.

```bash
sunholo swagger -h
usage: sunholo swagger [-h] [--vac_config_path VAC_CONFIG_PATH] [--agent_config_path AGENT_CONFIG_PATH]

optional arguments:
  -h, --help            show this help message and exit
  --vac_config_path VAC_CONFIG_PATH
                        Path to the vacConfig file. Set _CONFIG_FOLDER env var and place file in there to change default config location.
  --agent_config_path AGENT_CONFIG_PATH
                        Path to agentConfig file. Set _CONFIG_FOLDER env var and place file in there to change default config location.
```

### Example

Most often used to create a swagger.yaml file for use within deployments:

```sh
sunholo swagger > swagger.yaml 
```

Can also print to console:

```sh
sunholo swagger
host: ${_ENDPOINTS_HOST}
info:
  description: Multivac - Cloud Endpoints with a Cloud Run backend
  title: Multivac - Cloud Endpoints + Cloud Run
  version: 0.1.0
paths:
  /autogen/api/generate:
    post:
      operationId: post_autogen_invoke
      responses:
        '200':
          description: Default - A successful response
          schema:
            type: string
      summary: Post autogen_demo
      x-google-backend:
        address: https://autogen-xxxxx.a.run.app/api/generate
        protocol: h2
  /crewai/invoke_crewai:
    post:
      operationId: post_crewai_invoke
      responses:
        '200':
          description: Default - A successful response
          schema:
            type: string
      summary: Post trip_planner
...
```

By default `GET` requests are public, `POST` requests need an API key to access.  If you want to change that, list the endpoints under `get-auth` and `post-noauth` in your `agentConfig` eg:

```yaml
kind: agentConfig
apiVersion: v2
agents:
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

## sunholo vertex

This interacts with Google Vertex AI 

```shell
usage: sunholo vertex [-h] {create-extension,list-extensions} ...

positional arguments:
  {create-extension,list-extensions}
                        Vertex AI subcommands
    create-extension    Create a Vertex AI extension
    list-extensions     List all Vertex AI extensions

optional arguments:
  -h, --help            show this help message and exit
```

### sunholo vertex list-extensions

This lets you create and list Vertex AI extensions

```shell
sunholo --project your-project vertex list-extensions
[
    {
        'resource_name': 'projects/1232323/locations/us-central1/extensions/7454266623856214016',
        'display_name': 'Code Interpreter',
        'description': 'N/A'
    }
]
```

### sunholo vertex create-extension

This lets you upload the openapi config files to a bucket and deploy to Vertex AI Extensions

## sunholo llamaindex

This lets you work with LlamaIndex on Vertex corpus as per [https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/rag-api]

```shell
sunholo llamaindex -h  
usage: sunholo llamaindex [-h]
                          {create,delete,fetch,find,list,import_files,upload_file,upload_text}
                          ...

positional arguments:
  {create,delete,fetch,find,list,import_files,upload_file,upload_text}
                        LlamaIndex subcommands
    create              Create a new corpus
    delete              Delete a corpus
    fetch               Fetch a corpus
    find                Find a corpus
    list                List all corpus
    import_files        Import files from URLs to a corpus
    upload_file         Upload a local file to a corpus
    upload_text         Upload text to a corpus

optional arguments:
  -h, --help            show this help message and exit
```

## sunholo excel-init

Sets up Python files for use within a Excel Addon

#TODO - document how to set up in Excel

```shell
usage: sunholo excel-init [-h]
```

## sunholo tfvars

Edit `.tfvars` (or any HCL) files to help aid project init.

```sh
sunholo tfvars -h  
usage: sunholo tfvars [-h] {add} ...

positional arguments:
  {add}       TFVars subcommands
    add       Add or update an instance in a .tfvars file

optional arguments:
  -h, --help  show this help message and exit
```

Usage example, assuming you have a `terraform.tfvars` file to edit with a new Cloud Run instance called `new_service` with a json spec in `new_service.json` that looks something like:

```json
{
  "cpu": "1",
  "memory": "2Gi",
  "max_instance_count": 3,
  "timeout_seconds": 1500,
  "port": 8080,
  "service_account": "sa-newservice",
  "invokers": ["allUsers"],
  "cloud_build": {
    "included": ["application/new_service/**"],
    "path": "application/new_service/cloudbuild.yaml",
    "substitutions": {},
    "repo_name": "",
    "repo_owner": ""
  }
}

```

```sh
sunholo tfvars add terraform.tfvars cloud_run new_service --json-file=new_service.json --terraform-dir=/path/to/terraform/config
```

## sunholo tts

Text to speech via Google Cloud Speech API. It streams making an API call per sentence.

```sh
sunholo tts -h                                                          
usage: sunholo tts [-h] {speak,save} ...

positional arguments:
  {speak,save}  TTS subcommands
    speak       Convert text to speech and play it
    save        Convert text to speech and save to file

optional arguments:
  -h, --help    show this help message and exit
```

Usage example - can speak directly via your local audio device or save to a file:

```sh
# speaks if you have volume up
sunholo tts speak "hello world.  I'm the voice of the Multivac"

# saves to audio.wav file
sunholo tts save "hello world.  I'm the voice of the Multivac"

# read from file
sunholo tts speak --file README.md 
```

You can configure the language, gender, voice type as per: https://cloud.google.com/text-to-speech/docs/voices

```sh
usage: sunholo tts speak [-h] [--file] [--language LANGUAGE] [--voice-gender {NEUTRAL,MALE,FEMALE}] [--sample-rate SAMPLE_RATE]
                         [--voice_name VOICE_NAME]
                         text
```
            