---
title: Tool Orchestrator
sidebar_label: Orchestrator
sidebar_position: 2
---

# Tool Orchestrator

The `sunholo.tools.orchestrator` module provides async concurrent tool execution using `AsyncTaskRunner`, with config merging and result aggregation.

## ToolOrchestrator

Register tool handlers and execute them concurrently:

```python
from sunholo.tools.orchestrator import ToolOrchestrator

orchestrator = ToolOrchestrator(context="ui", max_concurrent=10)

# Register tools
orchestrator.register(
    "search",
    handler=search_handler,
    capability="Search the web for information",
    default_args={"max_results": 10},
)

orchestrator.register(
    "email",
    handler=email_handler,
    capability="Search email messages",
    default_args={"folder": "inbox"},
)

# List registered tools
tools = orchestrator.list_tools()
# [{"id": "search", "capability": "Search the web..."}, ...]
```

## Batch Execution

Execute multiple tools concurrently and get aggregated results:

```python
results = await orchestrator.run(
    tools=["search", "email"],
    question="Find recent reports about Q4",
    tool_configs={
        "search": {"max_results": 20},  # Override default
    },
    common_args={"user_id": "user@company.com"},
)

# results = {
#     "results": {"search": [...], "email": [...]},
#     "errors": {},
#     "completed": ["search", "email"],
# }
```

## Streaming Execution

Yield results as they complete using an async generator:

```python
async for event in orchestrator.run_streaming(
    tools=["search", "email", "calendar"],
    question="What meetings do I have today?",
):
    if event["type"] == "result":
        print(f"Tool {event['tool_id']} completed: {event['result']}")
    elif event["type"] == "error":
        print(f"Tool {event['tool_id']} failed: {event['error']}")
```

## Config Merging

Tool configs are merged from defaults and user overrides:

```python
merged = orchestrator.merge_tool_configs(
    tools=["search", "email"],
    user_configs={
        "search": {"max_results": 20, "language": "en"},
    },
)
# merged = {
#     "search": {"max_results": 20, "language": "en"},  # Default overridden
#     "email": {"folder": "inbox"},  # Defaults preserved
# }
```

Empty string and None values in user configs are ignored, preserving defaults.

## Context-Aware Timeouts

The `context` parameter configures timeout behavior via `AsyncTaskRunner`:

```python
# UI context: shorter timeouts for interactive use
ui_orchestrator = ToolOrchestrator(context="ui")

# Email context: longer timeouts for background processing
email_orchestrator = ToolOrchestrator(context="email")
```
