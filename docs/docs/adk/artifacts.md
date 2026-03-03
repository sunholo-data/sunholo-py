---
title: Artifact Service
sidebar_label: Artifacts
sidebar_position: 6
---

# Artifact Service

The `sunholo.adk.artifacts` module provides HTTP-based artifact persistence implementing ADK's `BaseArtifactService` interface. This enables agents to save and retrieve files, images, and other binary data.

## HttpArtifactService

A configurable HTTP artifact service with token refresh support:

```python
from sunholo.adk.artifacts import HttpArtifactService

service = HttpArtifactService(
    base_url="https://api.example.com",
    upload_path="/artifacts/upload",
    download_path="/artifacts/{artifact_id}",
    list_path="/artifacts/list",
    delete_path="/artifacts/{artifact_id}",
    token_provider=lambda: get_current_auth_token(),
)

# Upload an artifact
artifact_id = await service.save_artifact(
    app_name="my-app",
    user_id="user-123",
    session_id="session-456",
    filename="report.pdf",
    artifact=artifact_data,
)

# Download an artifact
data = await service.load_artifact(
    app_name="my-app",
    user_id="user-123",
    session_id="session-456",
    filename="report.pdf",
)

# List artifacts
artifacts = await service.list_artifacts(
    app_name="my-app",
    user_id="user-123",
    session_id="session-456",
)
```

## MimeRoutingArtifactService

Routes artifacts to different services based on MIME type - images go to one service, all other files to another:

```python
from sunholo.adk.artifacts import MimeRoutingArtifactService, HttpArtifactService

image_service = HttpArtifactService(
    base_url="https://images.example.com", ...
)
file_service = HttpArtifactService(
    base_url="https://files.example.com", ...
)

routing_service = MimeRoutingArtifactService(
    image_service=image_service,
    file_service=file_service,
)

# image/* MIME types go to image_service, everything else to file_service
```

## Configurable Field Names

The HTTP endpoints can use custom JSON field names to match your API:

```python
service = HttpArtifactService(
    base_url="https://api.example.com",
    upload_path="/files",
    id_field="file_id",        # Field name for artifact ID in responses
    name_field="file_name",    # Field name for filename
    items_field="files",       # Field name for list items
    scope_field="project_id",  # Field name for scoping
)
```
