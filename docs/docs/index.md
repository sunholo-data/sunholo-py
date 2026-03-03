---
sidebar_position: 1
slug: /
---
import AudioPlayer from '@site/src/components/audio';

# sunholo

A Python toolkit for building, configuring, and deploying GenAI applications. Sunholo provides a config-driven approach to working with multiple LLM providers, agent frameworks, and cloud infrastructure — letting you swap models, vectorstores, and deployment targets via YAML configuration rather than code changes.

<AudioPlayer src="https://storage.googleapis.com/sunholo-public-podcasts/sunholo-podcasts.wav" />

## Key Capabilities

- **Multi-provider GenAI** — Use Google Gemini, OpenAI, Anthropic, Ollama, and Azure through a unified interface
- **Agent frameworks** — Build agents with Google ADK, LangChain, or LlamaIndex
- **Config-driven architecture** — Define models, tools, permissions, and infrastructure in YAML
- **Cloud-native deployment** — Deploy to GCP Cloud Run, with AlloyDB vectorstores, Pub/Sub, and Firestore
- **Protocol support** — FastAPI services with streaming, MCP (Model Context Protocol), and A2A
- **Multi-channel messaging** — Connect agents to Email, Telegram, and WhatsApp

## Installation

```bash
pip install sunholo
```

Install with specific feature groups:

| Extra | Install command | What it adds |
|-------|----------------|--------------|
| `[all]` | `pip install sunholo[all]` | All dependencies |
| `[cli]` | `pip install sunholo[cli]` | [Command-line interface](cli) |
| `[gcp]` | `pip install sunholo[gcp]` | Google Cloud Platform integration |
| `[database]` | `pip install sunholo[database]` | [AlloyDB, Postgres, LanceDB](databases) |
| `[firestore]` | `pip install sunholo[firestore]` | [Firestore](databases/firestore) with circuit breaker |
| `[adk]` | `pip install sunholo[adk]` | [Google ADK](adk) agent framework |
| `[channels]` | `pip install sunholo[channels]` | [Email, Telegram, WhatsApp](channels) |
| `[openai]` | `pip install sunholo[openai]` | OpenAI provider |
| `[anthropic]` | `pip install sunholo[anthropic]` | Anthropic provider |
| `[pipeline]` | `pip install sunholo[pipeline]` | Chunking and embedding pipeline |
| `[http]` | `pip install sunholo[http]` | HTTP tools with retry |

## Module Overview

| Module | Description |
|--------|-------------|
| [`sunholo.agents`](agents) | FastAPI/Flask route handlers for GenAI services (VACs) |
| [`sunholo.adk`](adk) | Google ADK integration — agent config, sessions, events, MCP tools |
| [`sunholo.channels`](channels) | Multi-channel messaging — Email, Telegram, WhatsApp |
| [`sunholo.database`](databases) | Vector stores — AlloyDB, Postgres, LanceDB, Firestore, Supabase |
| [`sunholo.genai`](integrations) | Generic AI interface with extended thinking capture |
| [`sunholo.streaming`](howto/streaming) | Real-time response streaming |
| [`sunholo.tools`](tools) | Config-driven permissions and async tool orchestration |
| [`sunholo.auth`](config) | OAuth, RBAC, GCP/Azure authentication |
| [`sunholo.mcp`](agents) | Model Context Protocol server and client |
| [`sunholo.cli`](cli) | Command-line interface for chat, deploy, and config management |
| [`sunholo.integrations`](integrations) | LangChain, LlamaIndex, Vertex AI, Langfuse |

## Quick Example

Sunholo uses YAML configuration files to define your GenAI application. Access settings via `ConfigManager`:

```python
from sunholo.utils import ConfigManager

# Load configuration for a VAC (Virtual Agent Computer)
config = ConfigManager("my_agent")

# Access model settings from vac_config.yaml
llm = config.vacConfig("llm")          # e.g. "openai"
model = config.vacConfig("model")      # e.g. "gpt-4"
agent_type = config.vacConfig("agent") # e.g. "langchain"
```

Define your agent in `vac_config.yaml`:

```yaml
kind: vacConfig
apiVersion: v1
vac:
  my_agent:
    llm: openai
    model: gpt-4
    agent: langchain
    display_name: My Agent
    tags:
      - general
```

## What is Multivac?

Multivac is the full platform built on top of sunholo for deploying and managing GenAI applications at scale. It adds a web UI, user management, billing, and orchestration on Google Cloud Platform. See the [Multivac documentation](multivac) for more details.

## Running Tests

```bash
pip install pytest
pytest tests
```
