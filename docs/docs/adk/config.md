---
title: ADK Config
sidebar_label: Config
sidebar_position: 1
---

# ADK Config

The `sunholo.adk.config` module provides initialization and configuration for Google ADK applications, including session services, artifact services, and PostgreSQL advisory locks for safe concurrent access.

## ADKConfig

```python
from sunholo.adk.config import ADKConfig

config = ADKConfig(
    session_db_url="postgresql://user:pass@host/db",
    artifact_base_url="https://api.example.com",
)

# Initialize session service
session_service = config.create_session_service()

# Initialize artifact service
artifact_service = config.create_artifact_service()
```

## PostgreSQL Advisory Locks

For safe concurrent agent execution with shared session state:

```python
from sunholo.adk.config import ADKConfig

config = ADKConfig(session_db_url="postgresql://...")

# Advisory lock ensures only one agent accesses a session at a time
async with config.advisory_lock(session_id="user-123"):
    # Safe to read/write session state
    ...
```

## Configuration via ConfigManager

ADK config integrates with sunholo's `ConfigManager`:

```python
from sunholo.utils import ConfigManager

config = ConfigManager("my_vac")
adk_config = config.vacConfig("adk")

# adk_config might contain:
# {
#   "session_db_url": "postgresql://...",
#   "artifact_base_url": "https://...",
#   "model": "gemini-2.0-flash",
#   "sub_agents": ["search", "email"]
# }
```
