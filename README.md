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

4. **Deploy to Google Cloud Run:**
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
sunholo init <project-name>              # Create new project
sunholo list-configs                     # List all configurations
sunholo list-configs --validate          # Validate configs

# Development
sunholo vac chat <vac-name>             # Chat with a VAC locally
sunholo vac list                        # List available VACs
sunholo proxy start <service>           # Start local proxy to cloud service

# Deployment
sunholo deploy <vac-name>               # Deploy to Cloud Run
sunholo deploy <vac-name> --dev         # Deploy to dev environment

# Document Processing
sunholo embed <vac-name>                # Embed documents
sunholo merge-text <folder> <output>    # Merge files for context

# Cloud Services
sunholo discovery-engine create <name>   # Create Discovery Engine
sunholo proxy list                      # List running proxies
```

## 📝 Examples

### Vertex AI Chat with Memory

```python
from sunholo.utils import ConfigManager
from sunholo.components import pick_llm
from sunholo.agents import memory_client

config = ConfigManager('my-agent')
llm = pick_llm(config=config)
memory = memory_client(config=config)

# Chat with context
response = llm.invoke("What is Google Cloud?")
memory.add_message("user", "What is Google Cloud?")
memory.add_message("assistant", response)
```

### Document Processing with Discovery Engine

```python
from sunholo.discovery_engine import DiscoveryEngineClient
from sunholo.chunker import chunk_doc

# Initialize client
client = DiscoveryEngineClient(
    project_id='my-project',
    data_store_id='my-datastore'
)

# Process and index document
chunks = chunk_doc.chunk_file("document.pdf", chunk_size=1000)
client.import_documents(chunks)

# Search
results = client.search("What is the main topic?")
```

### Streaming Flask API

```python
from sunholo.agents import dispatch_to_qa

@app.route('/vac/streaming/<vac_name>', methods=['POST'])
def streaming_endpoint(vac_name):
    question = request.json.get('user_input')
    
    def generate():
        for chunk in dispatch_to_qa(
            question, 
            vac_name=vac_name,
            stream=True
        ):
            yield f"data: {chunk}\n\n"
    
    return Response(generate(), content_type='text/event-stream')
```

### Deploy from Template

```bash
# Create from template
sunholo init my-api --template agent

# Customize configuration
cd my-api
vi config/vac_config.yaml

# Test locally
sunholo vac chat my-agent --local

# Deploy to production
sunholo deploy my-agent
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