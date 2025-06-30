# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Sunholo-py Development Guide

## Project Overview
Sunholo-py is a comprehensive toolkit for deploying GenAI apps (VACs - Virtual Agent Computers) to Google Cloud Platform, with support for various LLMs, vectorstores, and deployment targets. The project follows a configuration-driven approach to enable rapid experimentation and deployment.

## Build & Test Commands
```bash
# Install package in dev mode
pip install -e ".[all]"  # or specific features: ".[test,gcp,langchain,azure,openai,anthropic]"

# Run all tests
pytest tests

# Run specific test files
pytest tests/test_config.py
pytest tests/test_async_genai2.py

# Run specific test function
pytest tests/test_config.py::test_load_config

# Run tests with coverage
pytest --cov=src/sunholo tests/

# Run type checking and linting
npm run lint        # If configured in package.json
npm run typecheck   # If configured in package.json
```

## Core Architecture

### Key Modules
- **agents**: Routing and dispatch for VAC agents (Flask/FastAPI routes, chat history, PubSub)
- **cli**: Command-line interface (chat, deploy, config management)
- **utils**: Configuration management via `ConfigManager` class
- **genai**: Generic AI interface supporting multiple providers (OpenAI, Anthropic, Google)
- **vertex**: Google Vertex AI integration with extensions
- **database**: Support for AlloyDB, PostgreSQL, LanceDB, Supabase
- **discovery_engine**: Google AI Search integration
- **langchain/llamaindex**: Framework integrations
- **mcp**: Model Context Protocol server and client integration (expose VACs as MCP tools)
- **streaming**: Real-time response streaming
- **chunker/embedder**: Document processing pipeline

### Configuration System
The project uses configuration files in the `config/` directory:
- `vac_config.yaml`: Main VAC configuration (models, agents, tools)
- `agent_config.yaml`: API endpoint routing
- `llm_config.yaml`: LLM provider settings
- `model_lookup.yaml`: Model name mappings across providers
- `prompt_config.yaml`: System prompts and templates

Access configs via:
```python
from sunholo.utils import ConfigManager
config = ConfigManager('your_vac_name')
llm = config.vacConfig('llm')
```

### CLI Usage
```bash
# List all configurations
sunholo list-configs

# Chat with a VAC
sunholo vac chat your_vac_name

# Deploy to Cloud Run
sunholo deploy your_vac_name

# Create new VAC from template
sunholo init your_vac_name
```

## Code Style
- **Imports**: Standard lib → Third-party → Local modules; group by category with blank lines
- **Typing**: Use type hints for function parameters and return values
- **Docstrings**: Google style docstrings with Args, Returns, Examples
- **Error handling**: Use try/except blocks with specific exceptions; log errors
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Structure**: Keep functions focused; follow single responsibility principle
- **Logging**: Use the custom logging module (`from sunholo.custom_logging import log`)

## License Header
All files should include the Apache 2.0 license header:
```python
#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
```

## Development Workflow

### Creating a New VAC
1. Use `sunholo init vac_name` to create from template
2. Configure in `config/vac_config.yaml`
3. Implement agent logic in the appropriate module
4. Test locally with `sunholo vac chat vac_name`
5. Deploy with `sunholo deploy vac_name`

### Common Tasks
- **Add new LLM provider**: Update `llm_config.yaml` and `model_lookup.yaml`
- **Create custom agent**: Inherit from base classes in `agents/`
- **Add vectorstore**: Configure in `vac_config.yaml` under `rag` section
- **Enable streaming**: Set `stream: true` in VAC config
- **Enable MCP server**: Set `enable_mcp_server=True` in VACRoutes for Claude Code integration
- **Add authentication**: Configure in `platform_config.yaml`

### Testing Guidelines
- Test files in `tests/` mirror source structure
- Use `pytest` fixtures for common setup
- Mock external services (GCP, APIs) in tests
- Test both sync and async code paths
- Verify configuration parsing and validation

## Environment Variables
Key environment variables:
- `VAC_CONFIG_FOLDER`: Location of config files
- `GCP_PROJECT`: Google Cloud project ID
- `GCP_REGION`: Default GCP region
- `LOG_LEVEL`: Logging verbosity

## Documentation
Full documentation at https://dev.sunholo.com/
Source docs in `docs/` using Docusaurus