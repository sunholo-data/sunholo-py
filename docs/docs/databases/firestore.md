---
title: Firestore
sidebar_label: Firestore
sidebar_position: 6
---

# Firestore

The `sunholo.database.firestore` module provides a production-hardened Google Cloud Firestore client with circuit breaker, retry logic, async/sync fallback, and context-aware timeouts.

Install with:
```bash
pip install sunholo[firestore]
```

## Quick Start

```python
from sunholo.database.firestore import get_firestore_client

# Get a robust Firestore client
client = get_firestore_client(project="my-gcp-project")

# Basic operations with automatic retry
doc = await client.get_document("collection", "doc-id")
await client.set_document("collection", "doc-id", {"key": "value"})
await client.update_document("collection", "doc-id", {"key": "new-value"})
await client.delete_document("collection", "doc-id")
```

## FirestoreClient

The `FirestoreClient` wraps the standard Firestore client with:

### Circuit Breaker

Prevents cascading failures by temporarily stopping requests when Firestore is unhealthy:

```python
from sunholo.database.firestore import FirestoreClient

client = FirestoreClient(
    project="my-project",
    circuit_breaker_threshold=5,    # Failures before opening circuit
    circuit_breaker_timeout=60,     # Seconds before retry
)
```

### Automatic Retry

Operations are retried with exponential backoff on transient errors:

```python
# Retries are automatic - just use the client normally
doc = await client.get_document("users", "user-123")
```

### Async/Sync Fallback

The client works in both async and sync contexts:

```python
# Async context
doc = await client.get_document("users", "user-123")

# Sync context (automatically detected)
doc = client.get_document_sync("users", "user-123")
```

### Context-Aware Timeouts

Timeouts adjust based on the execution context:

```python
from sunholo.utils.timeout_config import TimeoutConfig

config = TimeoutConfig(context="ui")       # Shorter timeouts for interactive use
config = TimeoutConfig(context="email")    # Longer timeouts for background processing
```

## Dependencies

- `google-cloud-firestore>=2.12.0`
- `google-api-core>=2.11.0`
- `tenacity>=8.2.0`
