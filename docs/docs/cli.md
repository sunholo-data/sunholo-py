# Sunholo CLI

A CLI is installed via `sunholo[cli]`

```bash
$> pip install sunholo[cli]

$> sunholo --help
usage: sunholo [-h] [--debug] [--project PROJECT] [--region REGION] {deploy,list-configs,init,merge-text,proxy,vac} ...

sunholo CLI tool for deploying GenAI VACs

optional arguments:
  -h, --help            show this help message and exit
  --debug               Enable debug output
  --project PROJECT     GCP project to list Cloud Run services from.
  --region REGION       Region to list Cloud Run services from.

commands:
  Valid commands

  {deploy,list-configs,init,merge-text,proxy,vac}
                        Commands
    deploy              Triggers a deployment of a VAC.
    list-configs        Lists all configuration files and their details
    init                Initializes a new Multivac project.
    merge-text          Merge text files from a source folder into a single output file.
    proxy               Set up or stop a proxy to the Cloud Run service.
    vac                 Interact with deployed VAC services.
```

## sunholo list-configs

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

The `sunholo proxy` command will let you proxy any Cloud Run service via [`gcloud run services proxy`](https://cloud.google.com/sdk/gcloud/reference/run/services/proxy) - you will need to authenticated with `gcloud` for the services you want to use.

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

usage: sunholo vac [-h] {list,get-url,chat} ...

positional arguments:
  {list,get-url,chat}  VAC subcommands
    list               List all VAC services.
    get-url            Get the URL of a specific VAC service.
    chat               Interact with a VAC service.

optional arguments:
  -h, --help           show this help message and exit
```

### Examples

For interactive sessions, it will start a proxy for you.  Use `exit` to break the session.

```bash

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

$> sunholo vac get-url edmonbrain
https://edmonbrain-xxxxxxxx.a.run.app

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
        sunholo vac chat edmonbrain 'hello, testing from ci/cd' --no-proxy --headless || exit 1
...
```
