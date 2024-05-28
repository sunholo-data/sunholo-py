# Sunholo CLI

A CLI is installed when you install the library:

```bash
pip install sunholo
sunholo --help
```

```
usage: sunholo [-h] {deploy,list-configs} ...

sunholo CLI tool for deploying GenAI VACs

optional arguments:
  -h, --help            show this help message and exit

commands:
  Valid commands

  {deploy,list-configs}
                        `sunholo deploy --help`
    deploy              Triggers a deployment of a VAC.
    list-configs        Lists all configuration files and their details.
```

## Config

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
```