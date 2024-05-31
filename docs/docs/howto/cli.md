# Sunholo CLI

A CLI is installed via `sunholo[cli]`

```bash
pip install sunholo[cli]

sunholo --help
usage: sunholo [-h] {deploy,list-configs,init,merge-text} ...

sunholo CLI tool for deploying GenAI VACs

optional arguments:
  -h, --help            show this help message and exit

commands:
  Valid commands

  {deploy,list-configs,init,merge-text}
                        Commands
    deploy              Triggers a deployment of a VAC.
    list-configs        Lists all configuration files and their details
    init                Initializes a new sunholo project.
    merge-text          Merge text files from a source folder into a single output file.
```

## Config

```bash
sunholo list-configs -h
usage: sunholo list-configs [-h] [--kind KIND] [--vac VAC] [--validate]

optional arguments:
  -h, --help   show this help message and exit
  --kind KIND  Filter configurations by kind e.g. `--kind=vacConfig`
  --vac VAC    Filter configurations by VAC name e.g. `--vac=edmonbrain`
  --validate   Validate the configuration files.
```

Examples:

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
      sunholo list-configs --kind=vacConfig --vac=${_SERVICE_NAME} --validate || exit 1
```

## Merge Text

Useful to turn a folder into one text file for large context windows.

```bash
sunholo merge-text -h 
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
