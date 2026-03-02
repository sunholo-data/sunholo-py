---
id: adk-index
title: ADK (Agent Development Kit)
sidebar_label: ADK
sidebar_position: 3
---

# ADK (Agent Development Kit)

The `sunholo.adk` module provides a generalized integration with [Google ADK](https://google.github.io/adk-docs/) for building multi-agent AI applications. It extracts production-tested patterns into reusable components for agent configuration, session management, event streaming, and tool integration.

Install with:
```bash
pip install sunholo[adk]
```

## Architecture Overview

The ADK module provides several layers of functionality:

```
sunholo.adk
├── config.py          # ADK initialization, session/artifact services
├── runner.py          # Dynamic agent runner, SubAgentRegistry, ModelRegistry
├── session.py         # Session creation with auth injection
├── events.py          # Event transformer (SSE tool feedback)
├── tools.py           # @mcp_tool decorator pattern
├── artifacts.py       # HTTP-based artifact service
└── litellm_compat.py  # Azure/LiteLLM compatibility layer
```

## Quick Start

### 1. Register and Run Agents

```python
from sunholo.adk.runner import SubAgentRegistry, ModelRegistry, DynamicRunner

# Create registries
agents = SubAgentRegistry()
models = ModelRegistry()

# Register agent factories
def create_search_agent():
    from google.adk.agents import Agent
    return Agent(name="search", model="gemini-2.0-flash", ...)

agents.register("search", factory=create_search_agent, capability="Search the web")

# Register models
models.register("gemini-2.0-flash", display_name="Gemini Flash")
models.register("gpt-4o", display_name="GPT-4o")

# Build and run
runner = DynamicRunner(agent_registry=agents, model_registry=models)
```

### 2. Session Management

```python
from sunholo.adk.session import SessionHelper, SessionKeys

helper = SessionHelper()
state = helper.build_session_state(
    user_id="user@example.com",
    auth_token="bearer_token_abc",
    config={"model": "gemini-2.0-flash"},
)
```

### 3. Event Streaming with Tool Feedback

```python
from sunholo.adk.events import EventTransformer, ToolFeedback, FeedbackType

transformer = EventTransformer()
transformer.register_tool_display("web_search", display_name="Web Search")

# Create tool feedback events for SSE streaming
event = ToolFeedback(
    tool_name="web_search",
    feedback_type=FeedbackType.START,
    message="Searching...",
)
sse_data = transformer.to_sse_event(event)
```

### 4. MCP Tool Decorator

```python
from sunholo.adk.tools import mcp_tool

@mcp_tool("search_docs", "Search documentation")
async def search_docs(query: str) -> str:
    """Search the documentation for relevant information."""
    results = await do_search(query)
    return format_results(results)
```

### 5. HTTP Artifact Service

```python
from sunholo.adk.artifacts import HttpArtifactService

service = HttpArtifactService(
    base_url="https://api.example.com",
    upload_path="/artifacts/upload",
    download_path="/artifacts/{artifact_id}",
    token_provider=lambda: get_auth_token(),
)
```

## Module Reference

- [ADK Config](./config.md) - Initialization, session services, advisory locks
- [Dynamic Runner](./runner.md) - Per-request agent creation, SubAgentRegistry, ModelRegistry
- [Session Helper](./session.md) - Auth injection, session state management
- [Event Transformer](./events.md) - Tool feedback events, SSE streaming
- [MCP Tools](./tools.md) - Tool decorator pattern for MCP integration
- [Artifact Service](./artifacts.md) - HTTP-based file/image persistence
- [LiteLLM Compatibility](./litellm-compat.md) - Azure/multi-model fixes

## Dependencies

The ADK module requires:
- `google-adk>=0.3.0` - Google Agent Development Kit
- `httpx>=0.25.0` - HTTP client for artifact services
- `litellm>=1.0.0` - Multi-model LLM support
- `fastmcp>=2.12.0` - MCP tool integration
