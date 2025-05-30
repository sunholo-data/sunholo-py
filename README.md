# Sunholo Python Library

[![PyPi Version](https://img.shields.io/pypi/v/sunholo.svg)](https://pypi.python.org/pypi/sunholo/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/pypi/pyversions/sunholo.svg)](https://pypi.python.org/pypi/sunholo/)

🚀 **AI DevOps framework for building GenAI applications on Google Cloud Platform**

Sunholo is a comprehensive Python framework that streamlines the development, deployment, and management of Generative AI applications (VACs - Virtual Agent Computers). It provides a configuration-driven approach with deep integration into Google Cloud services while supporting multiple AI providers.

## 🎯 What is Sunholo?

Sunholo helps you:
- 🤖 Build conversational AI agents with any LLM provider (Vertex AI, OpenAI, Anthropic, Ollama)
- ☁️ Deploy to Google Cloud Run with automatic scaling
- 🗄️ Use AlloyDB and Discovery Engine for vector storage and search
- 🔄 Handle streaming responses and async processing
- 📄 Process documents with chunking and embedding pipelines
- 🔧 Manage complex configurations with YAML files
- 🎨 Create APIs, web apps, and chat bots

## 🚀 Quick Start

### Prerequisites

Install [uv](https://docs.astral.sh/uv/) - a fast, modern Python package manager:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installation

```bash
# Install with CLI tools (recommended)
uv tool install --from "sunholo[cli]" sunholo

# Install with all features including GCP
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[all]"
```

### Your First VAC

1. **Initialize a new project:**
```bash
sunholo init my-ai-agent
cd my-ai-agent
```

2. **Configure your AI agent:**
Edit `config/vac_config.yaml`:
```yaml
kind: vacConfig
apiVersion: v1
vac:
  my-agent:
    llm: vertex
    model: gemini-1.5-pro
    agent: simple
    description: "My AI agent powered by Google Cloud"
```

3. **Chat with your agent locally:**
```bash
sunholo vac chat my-agent
```

4. **Run your agent as a local Flask app:**
```bash
sunholo deploy my-agent
```

## 📋 Features

### Core Capabilities

- **Multi-Model Support**: Integrate Vertex AI, OpenAI, Anthropic, Ollama in one app
- **Document Processing**: Chunk, embed, and index documents with Discovery Engine
- **Vector Databases**: Native support for AlloyDB, LanceDB, Supabase
- **Streaming**: Real-time response streaming for chat applications
- **Async Processing**: Pub/Sub integration for background tasks
- **Authentication**: Built-in Google Cloud IAM and custom auth

### Google Cloud Integration

- **Vertex AI**: Access Gemini, PaLM, and custom models
- **AlloyDB**: PostgreSQL-compatible vector database
- **Discovery Engine**: Enterprise search and RAG
- **Cloud Run**: Serverless deployment
- **Cloud Storage**: Document and file management
- **Pub/Sub**: Asynchronous message processing
- **Cloud Logging**: Centralized logging

### Framework Support

- **Web Frameworks**: Flask and FastAPI templates
- **AI Frameworks**: LangChain and LlamaIndex integration
- **Observability**: Langfuse for tracing and monitoring
- **API Standards**: OpenAI-compatible endpoints

## 🛠 Installation Options

### Using uv

```bash
# Core CLI features
uv tool install --from "sunholo[cli]" sunholo

# With Google Cloud Platform integration
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[gcp]"

# With specific LLM providers
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[openai]"
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[anthropic]"

# With database support
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[database]"

# Everything
uv tool install --from "sunholo[cli]" sunholo --with "sunholo[all]"
```

### Managing Installations

```bash
# Upgrade
uv tool upgrade sunholo

# List installed
uv tool list

# Uninstall
uv tool uninstall sunholo
```

### Development Setup

```bash
# Clone repository
git clone https://github.com/sunholo-data/sunholo-py.git
cd sunholo-py

# Install in development mode
uv venv
uv pip install -e ".[all]"

# Run tests
pytest tests/
```

## ⚙️ Configuration

Sunholo uses YAML configuration files:

```yaml
# config/vac_config.yaml
kind: vacConfig
apiVersion: v1
gcp_config:
  project_id: my-gcp-project
  location: us-central1
vac:
  my-agent:
    llm: vertex
    model: gemini-1.5-pro
    agent: langchain
    memory:
      - alloydb:
          project_id: my-gcp-project
          region: us-central1
          cluster: my-cluster
          instance: my-instance
    tools:
      - search
      - calculator
```

## 🔧 CLI Commands

```bash
# Project Management
sunholo init <project-name>              # Create new project from template
sunholo list-configs                     # List all configurations
sunholo list-configs --validate          # Validate configurations

# Development
sunholo vac chat <vac-name>             # Chat with a VAC locally
sunholo vac list                        # List available VACs  
sunholo vac get-url <vac-name>          # Get Cloud Run URL for a VAC
sunholo proxy start <service>           # Start local proxy to cloud service
sunholo proxy list                      # List running proxies
sunholo deploy <vac-name>               # Run Flask app locally

# Document Processing
sunholo embed <vac-name>                # Process and embed documents
sunholo merge-text <folder> <output>    # Merge files for context

# Cloud Services
sunholo discovery-engine create <name>   # Create Discovery Engine instance
sunholo vertex list-extensions          # List Vertex AI extensions
sunholo swagger <vac-name>              # Generate OpenAPI spec

# Integration Tools
sunholo excel-init                      # Initialize Excel plugin
sunholo llamaindex <query>              # Query with LlamaIndex
sunholo mcp list-tools                  # List MCP tools
sunholo tts <text>                      # Text-to-speech synthesis
```

## 📝 Examples

### Chat with History Extraction

```python
from sunholo.utils import ConfigManager
from sunholo.components import pick_llm
from sunholo.agents import extract_chat_history

config = ConfigManager('my-agent')
llm = pick_llm(config=config)

# Extract chat history from messages
chat_history = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]
history_str = extract_chat_history(chat_history)

# Use in prompt
response = llm.invoke(f"Given this history:\n{history_str}\n\nUser: How are you?")
```

### Document Processing with Chunker

```python
from sunholo.chunker import direct_file_to_embed
from sunholo.utils import ConfigManager

config = ConfigManager('my-agent')

# Process a file directly
result = direct_file_to_embed(
    "document.pdf",
    embed_prefix="doc",
    metadata={"source": "user_upload"},
    vectorstore=config.vacConfig("vectorstore")
)
```

### Vertex AI with Memory Tools

```python
from sunholo.vertex import get_vertex_memories
from sunholo.utils import ConfigManager

config = ConfigManager('my-agent')

# Get Vertex AI memory configuration
memory_config = get_vertex_memories(config)

# Use with Vertex AI
if memory_config:
    print(f"Memory tools configured: {memory_config}")
```

### Streaming Response with Flask

```python
from sunholo.agents import send_to_qa
from flask import Response, request

@app.route('/vac/streaming/<vac_name>', methods=['POST'])
def streaming_endpoint(vac_name):
    question = request.json.get('user_input')
    
    def generate():
        # Stream responses from the QA system
        response = send_to_qa(
            question, 
            vac_name=vac_name,
            stream=True
        )
        if hasattr(response, '__iter__'):
            for chunk in response:
                yield f"data: {chunk}\n\n"
        else:
            yield f"data: {response}\n\n"
    
    return Response(generate(), content_type='text/event-stream')
```

### Discovery Engine Integration

```python
from sunholo.discovery_engine import DiscoveryEngineClient

# Initialize client
client = DiscoveryEngineClient(
    project_id='my-project',
    data_store_id='my-datastore'
)

# Search documents
results = client.search("What is Vertex AI?")
for result in results:
    print(f"Content: {result.chunk.content}")
    print(f"Score: {result.relevance_score}")
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_config.py

# Run with coverage
pytest --cov=src/sunholo tests/

# Run async tests
pytest tests/test_async_genai2.py
```

## 📚 Documentation

- 📖 **Full Documentation**: https://dev.sunholo.com/
- 🎓 **Tutorials**: https://dev.sunholo.com/docs/howto/
- 🤖 **VAC Examples**: https://github.com/sunholo-data/vacs-public
- 🎧 **Audio Overview**: [Listen to the NotebookLM podcast](https://drive.google.com/file/d/1GvwRmiYDjPjN2hXQ8plhnVDByu6TmgCQ/view?usp=drive_link)

## 🤝 Contributing

We welcome contributions! See our [Contributing Guidelines](CONTRIBUTING.md).

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE.txt) file for details.

```
Copyright [2024] [Holosun ApS]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```

## 🙏 Support

- 📧 Email: multivac@sunholo.com
- 🐛 Issues: [GitHub Issues](https://github.com/sunholo-data/sunholo-py/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/sunholo-data/sunholo-py/discussions)
- 📖 Documentation: https://dev.sunholo.com/