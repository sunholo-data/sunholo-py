---
title: Tool Permissions
sidebar_label: Permissions
sidebar_position: 1
---

# Tool Permissions

The `sunholo.tools.permissions` module provides config-driven permission validation for tool access. It supports email-exact and domain-level matching, wildcard config parameters, time-based caching, and tag-based access control.

## permitted_tools

The core function for checking user permissions:

```python
from sunholo.tools.permissions import permitted_tools

rules = [
    {
        "domain": "company.com",
        "tools": ["search", "email"],
        "toolConfigs": {
            "search": {"max_results": 20},
            "email": {"send_limit": 50},
        },
    },
    {
        "email": "admin@company.com",
        "tools": ["search", "email", "admin"],
        "toolConfigs": {
            "admin": {"can_delete": True},
        },
    },
]

defaults = {
    "tools": ["search"],
    "toolConfigs": {"search": {"max_results": 10, "query": "*"}},
}

allowed, configs = permitted_tools(
    current_user={"email": "user@company.com"},
    requested_tools=["search", "email", "admin"],
    permission_rules=rules,
    default_permissions=defaults,
    tool_configs={"search": {"query": "my search"}},  # User-provided values
)
# allowed = ["search", "email"]  (admin not allowed for regular domain users)
# configs = {"search": {"max_results": 20, "query": "my search"}}
```

### How It Works

1. Start with default permissions (allowed tools + tool configs)
2. Apply matching permission rules (email-exact or domain matching)
3. Filter requested tools to the allowed set
4. Apply user-provided config values where defaults are wildcard (`"*"`) or unset

### Wildcard Config Values

Use `"*"` as a placeholder that users can override:

```python
defaults = {
    "tools": ["search"],
    "toolConfigs": {
        "search": {
            "query": "*",          # User MUST provide this
            "max_results": 10,     # User CANNOT override this
        }
    },
}

# User provides their own query
allowed, configs = permitted_tools(
    current_user={"email": "user@a.com"},
    requested_tools=["search"],
    default_permissions=defaults,
    tool_configs={"search": {"query": "latest reports"}},
)
# configs["search"]["query"] == "latest reports"
# configs["search"]["max_results"] == 10  (unchanged)
```

## PermissionCache

Time-based cache for permission results with configurable TTL:

```python
from sunholo.tools.permissions import PermissionCache

cache = PermissionCache(max_size=500, ttl_seconds=300)
cache.set("key", value)
result = cache.get("key")  # Returns None if expired
cache.clear()
```

## Tag-Based Access Control

Control tool access via tags with different access types:

```python
from sunholo.tools.permissions import check_tag_permissions, filter_tools_by_tags

tag_permissions = {
    "public": {"type": "public"},
    "internal": {"type": "domain"},
    "vip": {"type": "specific", "emails": ["vip@company.com"]},
    "partners": {"type": "domains", "domains": ["partner1.com", "partner2.com"]},
}

# Check if user can access a tagged resource
has_access = check_tag_permissions(
    user_email="user@company.com",
    tags=["internal"],
    tag_permissions=tag_permissions,
    owner_email="owner@company.com",
)

# Filter tools by their tags
tool_tags = {"search": ["public"], "admin": ["internal"], "billing": ["vip"]}
accessible = filter_tools_by_tags(
    user_email="user@company.com",
    requested_tools=["search", "admin", "billing"],
    tool_tags=tool_tags,
    tag_permissions=tag_permissions,
    owner_email="owner@company.com",
)
# accessible = ["search", "admin"]  (billing requires VIP)
```

### Access Types

| Type | Description |
|------|-------------|
| `public` | Anyone can access |
| `private` | Only the owner |
| `domain` | Same domain as the owner |
| `domains` | User's domain in an allowed list |
| `specific` | User's email in an allowed list |
| `group` | User in an allowed group (requires external resolution) |

## Batch Processing

Process multiple permission requests efficiently:

```python
from sunholo.tools.permissions import batch_permitted_tools

requests = [
    ({"email": "user1@a.com"}, ["search", "email"], None, "vac1"),
    ({"email": "user2@b.com"}, ["search"], None, "vac2"),
]

results = batch_permitted_tools(
    requests,
    permission_rules=rules,
    default_permissions=defaults,
)
# results = [(["search", "email"], {...}), (["search"], {...})]
```

## Email/Domain Matching

```python
from sunholo.tools.permissions import is_matching_email_or_domain

is_matching_email_or_domain("user@company.com", "user@company.com")  # True (exact)
is_matching_email_or_domain("user@company.com", "company.com")       # True (domain)
is_matching_email_or_domain("User@Company.COM", "company.com")       # True (case-insensitive)
is_matching_email_or_domain("user@other.com", "company.com")         # False
```
