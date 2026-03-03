---
title: Dynamic Runner
sidebar_label: Runner
sidebar_position: 2
---

# Dynamic Runner

The `sunholo.adk.runner` module provides the core agent orchestration system for Google ADK, enabling per-request agent creation with configurable models and sub-agents.

## SubAgentRegistry

Register agent factories that create ADK agent instances on demand. This avoids ADK's static caching issues where agents can only have one parent.

```python
from sunholo.adk.runner import SubAgentRegistry

registry = SubAgentRegistry()

# Register a default agent (included unless explicitly disabled)
registry.register(
    "search",
    factory=create_search_agent,
    capability="Search the web for information",
    is_default=True,
)

# Register an optional agent
registry.register(
    "admin",
    factory=create_admin_agent,
    capability="Administrative operations",
    is_default=False,
)

# Get default vs optional agents
default_ids = registry.get_default_ids()    # ["search"]
optional_ids = registry.get_optional_ids()  # ["admin"]

# Build capability text for agent instructions
capabilities = registry.build_capabilities_text()
# "- search: Search the web for information\n- admin: Administrative operations"

# Create a specific agent instance
agent = registry.create("search")
```

### Key Methods

| Method | Description |
|--------|-------------|
| `register(agent_id, factory, capability, is_default)` | Register an agent factory |
| `create(agent_id)` | Create an agent instance from its factory |
| `get_default_ids()` | List agents included by default |
| `get_optional_ids()` | List agents that must be explicitly enabled |
| `build_capabilities_text()` | Format capabilities for instructions |
| `build_delegations_text()` | Format delegation info for root agents |

## ModelRegistry

Manages model name to LLM instance mapping with caching and passthrough for Gemini models.

```python
from sunholo.adk.runner import ModelRegistry

models = ModelRegistry()

# Register named models
models.register("gemini-2.0-flash", display_name="Gemini Flash")
models.register("gpt-4o", display_name="GPT-4o")

# Gemini models pass through directly (no LiteLLM wrapper needed)
model = models.resolve("gemini-2.0-flash")  # Returns string "gemini-2.0-flash"

# Non-Gemini models get wrapped in LiteLLM
model = models.resolve("gpt-4o")  # Returns LiteLlm("gpt-4o") instance

# Custom passthrough prefixes
models = ModelRegistry(passthrough_prefixes=["gemini-", "vertex-"])
```

## DynamicRunner

Creates and runs ADK agents per-request, bypassing static caching.

```python
from sunholo.adk.runner import DynamicRunner

runner = DynamicRunner(
    agent_registry=agents,
    model_registry=models,
)
```

## build_instruction

Template-based instruction building with variable substitution.

```python
from sunholo.adk.runner import build_instruction

instruction = build_instruction(
    template="You are {name}. You help with {specialty}.",
    name="Assistant",
    specialty="data analysis",
)
# "You are Assistant. You help with data analysis."
```
