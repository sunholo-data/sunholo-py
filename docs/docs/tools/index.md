---
id: tools-index
title: Tools
sidebar_label: Tools
sidebar_position: 5
---

# Tools

The `sunholo.tools` module provides a tool management system for AI agents, including config-driven permissions, async orchestration, and tool execution.

## Modules

- [Permissions](./permissions.md) - Config-driven tool access control with email/domain matching and caching
- [Orchestrator](./orchestrator.md) - Async concurrent tool execution with config merging

## Quick Start

### Permission Checking

```python
from sunholo.tools.permissions import permitted_tools

# Define rules
rules = [
    {"domain": "company.com", "tools": ["search", "email", "calendar"]},
    {"email": "admin@company.com", "tools": ["search", "email", "calendar", "admin"]},
]

defaults = {
    "tools": ["search"],
    "toolConfigs": {"search": {"max_results": 10}},
}

# Check what tools a user can access
allowed, configs = permitted_tools(
    current_user={"email": "user@company.com"},
    requested_tools=["search", "email", "admin"],
    permission_rules=rules,
    default_permissions=defaults,
)
# allowed = ["search", "email"]
# configs = {"search": {"max_results": 10}}
```

### Tool Orchestration

```python
from sunholo.tools.orchestrator import ToolOrchestrator

orchestrator = ToolOrchestrator()
orchestrator.register("search", handler=search_fn, capability="Search the web")
orchestrator.register("email", handler=email_fn, capability="Read emails")

results = await orchestrator.run(
    tools=["search", "email"],
    question="Find recent reports",
)
# results = {"results": {...}, "errors": {...}, "completed": ["search", "email"]}
```
