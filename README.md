# sunholo-py

(draft release https://pypi.org/project/sunholo/ )

```sh
pip install sunholo
```

A python library to enable LLMOps within cloud environments

`sunholo` provides utilities to help manage LLM operations on Google Cloud Platform at first, but it is hoped that making it open source will help it support other clouds in the future.  A lot of the functionality is not Google Cloud Platform specific, so still may be helpful.

It is derived from the Edmonbrain project, the original blog post you can read here: https://code.markedmondson.me/running-llms-on-gcp/ and owes a lot to Langchain ( https://github.com/langchain-ai/langchain )

The package includes:

* `agents/` - functions for working with agents, including easy flask apps, parsing chat history and dispatching requests to different agent endpoints
* `archive/` - functions to record all Q&A activity to BigQuery via PubSub
* `bots/` - functions for special cases regrding frontend bots such as Web Apps, Discord and Slack
* `chunker/` - functions to slice up documents for sending into vector stores
* `components/` - functions to help configure which LLM, prompt, vectorstore or document retriever you will use based on a yaml config file
* `database/` - database setup functions and SQL to run on those sources such as Supabase
* `embedder/` - functions to send chunks into embedding vector stores
* `pubsub/` - use of PubSub for a message queue between components
* `qna/` - utilities for running agents such as retry strats and parsing of output/input
* `streaming/` - creation of streaming responses from LLM bots
* `summarise/` - creation of summaries of large documents
* `utils/` - reading configuration files, Google Cloud Platform metadata


```
   Copyright [2023] [Sunholo ApS]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```
