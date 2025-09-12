---
id: agents-index
title: Agents Documentation
sidebar_label: Agents
---

# Agents Documentation

This section covers the various agent implementations and routing systems in Sunholo.

## FastAPI Implementation

### Core Documentation
- [FastAPI VAC Routes](./fastapi-vac-routes.md) - Complete guide to using VACRoutesFastAPI
- [FastAPI Examples](./fastapi-examples.md) - Example code and demos
- [Implementation Summary](./FASTAPI_IMPLEMENTATION_SUMMARY.md) - Technical details of the FastAPI implementation

### Quick Start

```bash
# Run the standalone demo (no installation required)
uv run examples/fastapi_vac_demo_standalone.py

# Or with full sunholo features
uv pip install -e ".[fastapi]"
uv run examples/fastapi_vac_demo.py
```

## Flask Implementation

The original Flask-based VAC routes are still available and fully supported. Both Flask and FastAPI implementations share the same callback-based streaming pattern, making migration straightforward.

## Key Features

- ✅ **Callback-based streaming** - Works with any LLM that uses callbacks
- ✅ **Async/sync support** - Automatic detection and handling
- ✅ **Multiple formats** - Plain text and SSE streaming
- ✅ **OpenAI compatibility** - Drop-in replacement for OpenAI API
- ✅ **MCP server support** - Integration with Claude Code

## Choosing Between Flask and FastAPI

### Use FastAPI when:
- Building new applications
- Need async-first design
- Want better performance at scale
- Using modern Python (3.9+)

### Use Flask when:
- Working with existing Flask apps
- Need simpler, synchronous code
- Have Flask-specific middleware
- Team is more familiar with Flask

## Migration Guide

Migrating from Flask to FastAPI is straightforward:

```python
# Flask
from sunholo.agents.flask import VACRoutes
app = Flask(__name__)
vac_routes = VACRoutes(app, interpreter)

# FastAPI
from sunholo.agents.fastapi import VACRoutesFastAPI
app = FastAPI()
vac_routes = VACRoutesFastAPI(app, interpreter)
```

The interpreter functions and callback patterns remain identical!