---
sidebar_position: 1
slug: /
---

# Introduction

Welcome to the dev portal for the `sunholo` project, which is the open-source component for the Sunholo Multivac.

`sunholo` is a library of helpful utilities for deploying GenAI applications on the cloud.  It includes various python modules and functions that have been needed to help develop GenAI applications called VACs (Virtual Agent Computers) on the Multivac system.  Whilst its primary purpose is to enable Multivac applications, it may also be useful for more general GenAI applications, for instance if you are looking for ways to manage many GenAI configurations.


## Skills needed

To start using the package, a good background is:

* Basic Python skills
* Knowledge about GenAI models and components such as vectorstores
* Can deploy a [Langchain Langserve template](https://templates.langchain.com/) locally
* Familiar with cloud providers, in particular Google Cloud Platform

If you have the above, then you should be able to get some value from the `sunholo` package.

## Getting started

`sunholo` is available on pip https://pypi.org/project/sunholo/ 

Minimal deps:

```sh
pip install sunholo
```

All dependencies:

```sh
pip install sunholo[all]
```

Database functions:

```sh
pip install sunholo[database]
```

Google Cloud Platform:

```sh
pip install sunholo[gcp]
```

OpenAI

```sh
pip install sunholo[openai]
```

Anthropic

```sh
pip install sunholo[anthropic]
```       

HTTP tools

```sh
pip install sunholo[http]
```

Sunholo is derived from the Edmonbrain project, the original blog post you can read here: https://code.markedmondson.me/running-llms-on-gcp/ and owes a lot to Langchain ( https://github.com/langchain-ai/langchain )

The package includes:

* `agents/` - functions for working with agents, including easy flask apps, parsing chat history and dispatching requests to different agent endpoints
* `archive/` - functions to record all Q&A activity to BigQuery via PubSub
* `bots/` - functions for special cases regarding frontend bots such as GChat, Web Apps, Discord and Slack
* `chunker/` - functions to slice up documents for sending into vector stores
* `components/` - functions to help configure which LLM, prompt, vectorstore or document retriever you will use based on a yaml config file
* `database/` - database setup functions and SQL to run on those sources such as Supabase or PostgreSQL
* `embedder/` - functions to send chunks into embedding vector stores
* `pubsub/` - use of PubSub for a message queue between components
* `qna/` - utilities for running agents such as retry strats and parsing of output/input
* `streaming/` - creation of streaming responses from LLM bots
* `summarise/` - creation of summaries of large documents
* `utils/` - reading configuration files, Google Cloud Platform metadata