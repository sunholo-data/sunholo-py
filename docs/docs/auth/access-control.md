---
title: Access Control
sidebar_label: Access Control
sidebar_position: 2
---

# Access Control

The `sunholo.auth.access_control` module provides a declarative access control system for restricting access to resources based on user identity.

## AccessControl

Manage rules for multiple resources:

```python
from sunholo.auth.access_control import AccessControl, AccessLevel

ac = AccessControl()

# Public resource - anyone can access
ac.add_rule("public-api", AccessLevel.PUBLIC)

# Domain-restricted - same company domain only
ac.add_rule("internal-tools", AccessLevel.DOMAIN, domain="company.com")

# Specific users only
ac.add_rule("admin-panel", AccessLevel.SPECIFIC, emails=["admin@company.com"])

# Multiple domains
ac.add_rule("partner-portal", AccessLevel.DOMAINS, domains=["company.com", "partner.com"])

# Group-based
ac.add_rule("team-dashboard", AccessLevel.GROUP, groups=["engineering", "product"])

# Role-based
ac.add_rule("superuser-tools", AccessLevel.ROLE, roles=["admin", "superuser"])

# Private - owner only
ac.add_rule("my-draft", AccessLevel.PRIVATE, owner_email="author@company.com")
```

## Checking Access

```python
# Simple check
if ac.check_access("internal-tools", user_email="user@company.com"):
    print("Access granted")

# With groups and roles
if ac.check_access(
    "team-dashboard",
    user_email="user@company.com",
    user_groups={"engineering"},
    user_roles={"developer"},
):
    print("Access granted")

# No rules = open access
ac.check_access("unprotected-resource", user_email="anyone@any.com")  # True
```

## Filtering Resources

Filter a list of resources to those a user can access:

```python
all_resources = ["public-api", "internal-tools", "admin-panel", "partner-portal"]

accessible = ac.filter_resources(
    all_resources,
    user_email="user@company.com",
)
# ["public-api", "internal-tools"]  (admin-panel excluded)
```

## Multiple Rules (OR Logic)

When multiple rules exist for a resource, access is granted if ANY rule matches:

```python
# Both specific users AND domain users can access
ac.add_rule("shared-resource", AccessLevel.SPECIFIC, emails=["vip@external.com"])
ac.add_rule("shared-resource", AccessLevel.DOMAIN, domain="company.com")

ac.check_access("shared-resource", user_email="vip@external.com")    # True
ac.check_access("shared-resource", user_email="user@company.com")    # True
ac.check_access("shared-resource", user_email="random@other.com")    # False
```

## Config-Driven Setup

Load access rules from a configuration dictionary:

```python
config = {
    "internal-tools": {"level": "domain", "domain": "company.com"},
    "admin-panel": [
        {"level": "specific", "emails": ["admin@company.com"]},
        {"level": "role", "roles": ["superuser"]},
    ],
    "public-api": {"level": "public"},
}

ac = AccessControl.from_config(config)
```

This integrates well with YAML configuration files:

```yaml
# access_control.yaml
internal-tools:
  level: domain
  domain: company.com
admin-panel:
  - level: specific
    emails:
      - admin@company.com
  - level: role
    roles:
      - superuser
public-api:
  level: public
```

## AccessLevel Enum

| Level | Description |
|-------|-------------|
| `PUBLIC` | Anyone can access (including anonymous) |
| `PRIVATE` | Only the resource owner |
| `DOMAIN` | Users with the same email domain |
| `DOMAINS` | Users from a list of allowed domains |
| `SPECIFIC` | Users from a list of allowed emails |
| `GROUP` | Users in allowed groups |
| `ROLE` | Users with allowed roles |

## Managing Rules

```python
# List all rules
all_rules = ac.list_rules()

# List rules for a specific resource
resource_rules = ac.list_rules("admin-panel")

# Remove all rules for a resource
ac.remove_rules("admin-panel")
```
