# Pirate Talk

This VAC is a 'hello world' Langserve app that is taken from the official [pirate_talk Langserve template](https://templates.langchain.com/?integration_name=pirate-speak). 

It demonstrates how to deploy a Langserve application on Multivac, and the configuration needed.  Its a good starter VAC to try first.

## Summary

This VAC application translates your questions into pirate speak! Ohh arr.

![](vac-pirate-speak.png)

## Config yaml

An explanation of the configuration is below:

* `vac.pirate_speak` - this is the key that all other configurations are derived from, referred to as "vector_name"
* `llm`: The configuration specifies an LLM model.  You can swap this for any model supported by `sunholo` so that it can work with the `pick_llm()` function via `model = pick_llm("pirate_speak")`.
* `agent`: Required to specify what type of agent this VAC is, which determines which Cloud Run or other runtime is queried via the endpoints
* `display_name`: Used by end clients such as the webapp for the UI.
* `avatar_url`: Used by end clients such as the webapp for the UI.
* `description`: Used by end clients such as the webapp for the UI.
* `tags`: Used to specify which users are authorized to see this VAC, defined via `users_config.yaml`

```yaml
kind: vacConfig
apiVersion: v1
vac:
    pirate_speak:
        llm: openai
        agent: langserve
        #agent_url: you can specify manually your URL endpoint here, or on Multivac it will be populated automatically
        display_name: Pirate Speak
        tags: ["free"] # for user access, matches users_config.yaml
        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4
        description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that will repeat back what you say but in a pirate accent.  Ooh argh me hearties!  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.
```
