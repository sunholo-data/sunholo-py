# Sunholo Components

This folder contains several Python files that define various functions used in the Sunholo project. Here is a brief overview of each file and the functions it contains:

## llm.py

This file contains functions related to Language Learning Models (LLMs). The functions include:

- pick_llm: Picks an LLM based on the vector_name parameter.
- pick_streaming: Returns a boolean value based on the llm_str parameter.
- get_llm: Configures LLMs based on the llm_str parameter.
- get_llm_chat: Configures LLMs for chat based on the llm_str parameter.
- get_embeddings: Picks an embedding based on the llm_str parameter.
- pick_embedding: Configures embeddings based on the llm_str parameter.

## prompt.py

This file contains functions related to prompts. The functions include:

- pick_prompt: Picks a custom prompt based on the vector_name parameter.
- pick_chat_buddy: Picks a chat buddy based on the vector_name parameter.
- pick_agent: Returns a boolean value based on the agent_str parameter.
- pick_shared_vectorstore: Picks a shared vectorstore based on the vector_name and embeddings parameters.
- get_chat_history: Gets the chat history based on the inputs and vector_name parameters.

## retriever.py

This file contains functions related to retrievers. The functions include:

- load_memories: Loads memories based on the vector_name parameter.
- pick_retriever: Picks a retriever based on the vector_name and embeddings parameters.

## vectorstore.py

This file contains functions related to vectorstores. The functions include:

- pick_vectorstore: Picks a vectorstore based on the vs_str, vector_name, and embeddings parameters.
- load_memories: Loads memories based on the vector_name parameter.