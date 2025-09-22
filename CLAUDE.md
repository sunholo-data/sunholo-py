# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Sunholo-py Development Guide

## Project Overview
Sunholo-py is a comprehensive toolkit for deploying GenAI apps (VACs - Virtual Agent Computers) to Google Cloud Platform, with support for various LLMs, vectorstores, and deployment targets. The project follows a configuration-driven approach to enable rapid experimentation and deployment.

## Build & Test Commands
```bash
# Clean up stale installations (run if version mismatches occur)
./scripts/clean-egg-info.sh

# Install dependencies with uv (ALWAYS use uv, never use pip directly)
uv pip install -e ".[all]"  # or specific features: ".[test,gcp,langchain,azure,openai,anthropic,fastapi]"

# Run all tests
uv run pytest tests

# Run specific test files
uv run pytest tests/test_config.py
uv run pytest tests/test_async_genai2.py
uv run pytest tests/test_vac_routes_fastapi.py

# Run specific test function
uv run pytest tests/test_config.py::test_load_config

# Run tests with coverage
uv run pytest --cov=src/sunholo tests/

# Install specific packages
uv pip install fastapi httpx

# Run FastAPI demos and tests
python examples/fastapi_vac_demo.py               # Full demo with all features
python examples/fastapi_vac_demo.py --sync        # Test with sync interpreters
uv run examples/fastapi_vac_demo_standalone.py    # Standalone demo with inline dependencies

# Test SSE streaming endpoint
curl -X POST http://localhost:8000/vac/streaming/demo/sse \
    -H "Content-Type: application/json" \
    -d '{"user_input": "Tell me a story"}'

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

### Type Hints with Optional Dependencies
Many modules in this codebase have optional dependencies. We want to add comprehensive type hints throughout the codebase but haven't fully done so yet due to import issues with optional packages. When adding type hints for optional dependencies, use this pattern:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from optional_package import OptionalType

try:
    from optional_package import OptionalType
    PACKAGE_AVAILABLE = True
except ImportError:
    OptionalType = None
    PACKAGE_AVAILABLE = False

# Now you can use OptionalType in type hints without import errors
def my_function(param: OptionalType) -> None:
    if not PACKAGE_AVAILABLE:
        raise ImportError("optional_package required. Install with: pip install sunholo[extra]")
    # ... use param
```

This pattern ensures:
- Type hints are preserved for IDE support and documentation
- No import errors when optional dependencies are missing
- Type checkers can still validate the code properly

Please help add these type hints throughout the codebase where they're currently missing, especially in modules with optional dependencies like FastAPI, Flask, LangChain, LlamaIndex, etc.

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
- **Enable MCP server**: Set `enable_mcp_server=True` in VACRoutes (Flask) or VACRoutesFastAPI (FastAPI) for Claude Code integration
- **Add authentication**: Configure in `platform_config.yaml`
- **Use FastAPI for async**: Use `VACRoutesFastAPI` from `sunholo.agents.fastapi` for async-first applications

### Testing Guidelines
- Test files in `tests/` mirror source structure
- Use `pytest` fixtures for common setup
- Mock external services (GCP, APIs) in tests
- Test both sync and async code paths
- Verify configuration parsing and validation

## Common Issues & Solutions

### Version Mismatch
If `sunholo -v` shows an old version after updating:
1. Run `./scripts/clean-egg-info.sh` to remove stale egg-info directories
2. Reinstall with `uv pip install -e .`
3. Verify with `sunholo -v`

See `docs/troubleshooting/version-mismatch.md` for detailed troubleshooting.

### Important Notes
- **ALWAYS use uv for package management**, never use pip directly
- **Never hardcode version-specific URLs** in pyproject.toml
- **Run cleanup script** when encountering version issues

## Environment Variables
Key environment variables:
- `VAC_CONFIG_FOLDER`: Location of config files
- `GCP_PROJECT`: Google Cloud project ID
- `GCP_REGION`: Default GCP region
- `LOG_LEVEL`: Logging verbosity

## Documentation
Full documentation at https://dev.sunholo.com/
Source docs in `docs/` using Docusaurus