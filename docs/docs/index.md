---
sidebar_position: 1
slug: /
---

# Introduction

Welcome to the dev portal for the `sunholo` project, which is the open-source component for the Sunholo Multivac.

`sunholo` is a library of helpful utilities for deploying GenAI applications on the cloud.  It includes various python modules and functions that have been needed to help develop GenAI applications called VACs (Virtual Agent Computers) on the Multivac system.  Whilst its primary purpose is to enable Multivac applications, it may also be useful for more general GenAI applications, for instance if you are looking for ways to manage many GenAI configurations.

## Listen to the audio file:

A [NotebookLM](https://notebooklm.google/) generated podcast of the codebase that may help give you an overview of what the library is capable of:

<iframe
   frameborder="0"
   width="500"
   height="100"
   src="https://drive.google.com/file/d/1GvwRmiYDjPjN2hXQ8plhnVDByu6TmgCQ/preview?usp=drive_link">
</iframe>

[Alternatively, listen to the audio file on Google Drive](https://drive.google.com/file/d/1GvwRmiYDjPjN2hXQ8plhnVDByu6TmgCQ/view?usp=drive_link) 

> "Ever wish you could build your own AI?..."


## Skills needed

To start using the package, a good background is:

* Basic Python skills
* Knowledge about GenAI models and components such as vectorstores
* Can deploy a GenAI application, such as a Langchain Langserve template or a LlamaIndex app.
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

Sunholo [CLI](cli):

```sh
pip install sunholo[cli]
```

[Databases](databases):

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

Chunking and embedding pipeline

```sh
pip install sunholo[pipeline]
```

## Tests via pytest

If loading from GitHub, run tests:

```bash
pip install pytest
pip install . --use-feature=in-tree-build
pytest tests
```

## Legacy

Sunholo is derived from the Edmonbrain project, the original blog post you can read here: https://code.markedmondson.me/running-llms-on-gcp/ and owes a lot to Langchain ( https://github.com/langchain-ai/langchain )
