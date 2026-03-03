---
id: auth-index
title: Authentication & Access Control
sidebar_label: Auth
sidebar_position: 6
---

# Authentication & Access Control

The `sunholo.auth` module provides authentication and access control for sunholo applications.

## Modules

| Module | Description |
|--------|-------------|
| `auth.run` | GCP Cloud Run token management |
| `auth.gcloud` | Local gcloud token retrieval |
| `auth.oauth` | [Google OAuth2](./oauth.md) flow with token caching |
| `auth.access_control` | [Declarative RBAC](./access-control.md) for resource access |

## Quick Start

### OAuth2 Authentication

```python
from sunholo.auth.oauth import GoogleAuthManager

auth = GoogleAuthManager(
    client_id="your-client-id",
    client_secret="your-client-secret",
    scopes=["openid", "email", "profile"],
)

# Get or refresh credentials
credentials = await auth.get_credentials(user_id="user@example.com")
```

### Access Control

```python
from sunholo.auth.access_control import AccessControl, AccessLevel

ac = AccessControl()
ac.add_rule("internal-tools", AccessLevel.DOMAIN, domain="company.com")
ac.add_rule("admin-panel", AccessLevel.SPECIFIC, emails=["admin@company.com"])

# Check access
if ac.check_access("internal-tools", user_email="user@company.com"):
    # Grant access
    ...

# Filter resources
allowed = ac.filter_resources(
    ["internal-tools", "admin-panel", "public-api"],
    user_email="user@company.com",
)
```

### Cloud Run Tokens

```python
from sunholo.auth import get_header, get_cloud_run_token

# Get auth header for Cloud Run service calls
header = get_header("https://my-service-abc123-uc.a.run.app")
```
