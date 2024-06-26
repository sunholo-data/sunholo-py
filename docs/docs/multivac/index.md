# Multivac Cloud

The `sunholo` library takes care of code within the Virtual Agent Computer (VAC) applications.  

The [VAC](../VACs) is an abstraction that offers a standard way to interact with GenAI applications.  The advantage of this is that the input and output of those systems can be standardised and can help speed up deployments.  Within a VAC you can use frameworks such as Langchain, LlamaIndex, VertexAI, OpenAI, or your own custom libraries, in any language so long as it can be used within a Docker container.

Multivac (Multi-VAC) Cloud is an implementation of this abstraction.  It consists of Infrastructure-as-Code (IAC) to provision Cloud services that the VACs can plug into.  The [YAML configuration files](../config) is the link between what is internal to a VAC and what is external within the cloud environment.

## Multivac features

Each VAC can reach all the cloud services within the Multivac, which is geared towards enterprise production purposes.  Principal aims are:

* To be as serverless as possible 
    - we don't want to babysit servers, we do want to scale to 0 but be able to handle high peaks in traffic
* To be as secure as possible
    - the greatest value for GenAI applications is your data, so safeguarding that data within a Virtual Private Cloud and other security measures are prioritised.
* To have flexible user interfaces
    - the most impactful way for your GenAI application to be a success will be how users can experience the GenAI outputs.  Having flexibility on whether this is a video, API, chat bot or terminal call helps integrate the solution wherever it makes the most sense

Keeping those principles in mind, the current implementation uses Google Cloud Platform with these combined services:

* Cloud Run providing microservices running each VAC
* Virtual Private Cloud (VPC) perimeter on all Multivac services
* Vertex AI - GenAI models via Model Garden and integration with continuously evolving GenAI services
* Gemini API - world-class GenAI model, working alongside similar models such as OpenAI and Anthropic.
* Cloud Storage buckets for file sinks - anything that can write to a bucket can be processed
* Cloud Endpoints - providing API keys, quotas and limits for all microservices
* Pub/Sub - asynchronous message queues for highly parallel data processing pipelines
* GitHub/Cloud Build - fully automatic CI/CD pipelines deploying to dev/test/prod destinations upon commit
* Secret Manager - secure storage of all API secrets 
* AlloyDB - flexible and fast PostgreSQL compatible solution for embeddings, chat history, analytics
* BigQuery - data lake and structured logging support
* Cloud Logging and GenAI analytics and eval tools for application iterations.

## User Interfaces

A focus for Multivac is providing flexible user interfaces for GenAI applications.  So far this includes:

* A Web Application using Chainlit found at https://multivac.sunholo.com
* API access to underlying VAC microservices when you have been issued a `MULTIVAC_API_KEY`
* Terminal Command Line Interface (CLI) via the `sunholo[cli]` extension
* Chat bot interfaces such as Discord, GChat and Teams
* Streaming audio/video via LiveKit integrations
* Desktop client applications via tools such as https://jan.ai
* Any OpenAPI compatible tool will work with a VAC API call - even if you are calling a non-OpenAI model.  

An individual VAC could also create its own UI, since its being served via a HTTP container.

Get in touch if you would like to see other ways to interact with GenAI!   

## Data Integrations

The tools above are for data outputs, but for inputting data so that you can tailor your model responses (such as for Reterival Augment Generation or RAG) there are extensive pipelines available.  See the [embedding](../howto/embedding) section for more details.  

* Google Cloud Storage buckets can store data such as documents, videos and audio.
* PostgreSQL databases can store embeddings via `pgvector` and other useful GenAI features such as logging and chat history.
* Specialised GenAI databases such as vector stores and document retrieval


## Using Multivac Cloud

The Multivac Cloud provides an API key `MULTIVAC_API_KEY` which enables access to the private services.  This is available upon request.  You can use the API key to access VACs more advanced than the free VACs available at the https://multivac.sunholo.com web portal.

## Using your own cloud

All services are deployable on your own cloud for complete ownership.  This is only available to partners working with Holosun ApS.  Get in touch if you would like to explore being a partner.