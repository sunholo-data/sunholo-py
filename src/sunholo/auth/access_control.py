#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
User and group based access control.

Provides a declarative access control system for restricting access to
resources (VACs, tools, data, etc.) based on user identity:

- Email-exact matching
- Domain-level matching
- Group membership
- Role-based access control (RBAC)
- Public/private access levels

Usage:
    from sunholo.auth.access_control import AccessControl, AccessLevel

    ac = AccessControl()
    ac.add_rule("admin-tools", AccessLevel.SPECIFIC, emails=["admin@company.com"])
    ac.add_rule("internal-docs", AccessLevel.DOMAIN, domain="company.com")

    if ac.check_access("admin-tools", user_email="admin@company.com"):
        # grant access
        ...
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class AccessLevel(str, Enum):
    """Access level types for resources."""

    PUBLIC = "public"
    PRIVATE = "private"
    DOMAIN = "domain"
    DOMAINS = "domains"
    SPECIFIC = "specific"
    GROUP = "group"
    ROLE = "role"


@dataclass
class AccessRule:
    """A single access control rule.

    Attributes:
        resource_id: The resource this rule applies to.
        level: The access level type.
        owner_email: Email of the resource owner (for PRIVATE/DOMAIN).
        domain: Single domain to allow (for DOMAIN level).
        domains: List of allowed domains (for DOMAINS level).
        emails: List of allowed emails (for SPECIFIC level).
        groups: List of allowed groups (for GROUP level).
        roles: List of allowed roles (for ROLE level).
        metadata: Additional rule metadata.
    """

    resource_id: str
    level: AccessLevel = AccessLevel.PUBLIC
    owner_email: str = ""
    domain: str = ""
    domains: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def extract_domain(email: str) -> Optional[str]:
    """Extract the domain from an email address.

    Args:
        email: Email address string.

    Returns:
        Lowercase domain, or None if invalid.
    """
    if not email or "@" not in email:
        return None
    return email.lower().split("@")[1]


def check_access(
    rule: AccessRule,
    user_email: Optional[str] = None,
    user_groups: Optional[Set[str]] = None,
    user_roles: Optional[Set[str]] = None,
) -> bool:
    """Check if a user has access based on a single rule.

    Args:
        rule: The access rule to check against.
        user_email: The user's email address.
        user_groups: Set of groups the user belongs to.
        user_roles: Set of roles the user has.

    Returns:
        True if the user has access.
    """
    if rule.level == AccessLevel.PUBLIC:
        return True

    email = (user_email or "").lower()

    if rule.level == AccessLevel.PRIVATE:
        if not email:
            return False
        return email == rule.owner_email.lower()

    if rule.level == AccessLevel.DOMAIN:
        if not email:
            return False
        user_domain = extract_domain(email)
        rule_domain = rule.domain.lower() if rule.domain else extract_domain(rule.owner_email)
        return bool(user_domain and rule_domain and user_domain == rule_domain)

    if rule.level == AccessLevel.DOMAINS:
        if not email:
            return False
        user_domain = extract_domain(email)
        allowed = {d.lower() for d in rule.domains}
        return bool(user_domain and user_domain in allowed)

    if rule.level == AccessLevel.SPECIFIC:
        if not email:
            return False
        allowed = {e.lower() for e in rule.emails}
        return email in allowed

    if rule.level == AccessLevel.GROUP:
        if not user_groups:
            return False
        allowed = set(rule.groups)
        return bool(user_groups & allowed)

    if rule.level == AccessLevel.ROLE:
        if not user_roles:
            return False
        allowed = set(rule.roles)
        return bool(user_roles & allowed)

    return False


class AccessControl:
    """Manages access control rules for multiple resources.

    Maintains a registry of access rules and provides methods
    to check and filter access for users.

    Usage:
        ac = AccessControl()
        ac.add_rule("my-vac", AccessLevel.DOMAIN, domain="company.com")
        ac.add_rule("admin-panel", AccessLevel.SPECIFIC, emails=["admin@co.com"])

        if ac.check_access("my-vac", user_email="user@company.com"):
            ...

        allowed = ac.filter_resources(
            ["my-vac", "admin-panel", "public-api"],
            user_email="user@company.com",
        )
    """

    def __init__(self):
        self._rules: Dict[str, List[AccessRule]] = {}

    def add_rule(
        self,
        resource_id: str,
        level: AccessLevel | str = AccessLevel.PUBLIC,
        owner_email: str = "",
        domain: str = "",
        domains: List[str] | None = None,
        emails: List[str] | None = None,
        groups: List[str] | None = None,
        roles: List[str] | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """Add an access rule for a resource.

        Multiple rules can be added per resource. Access is granted
        if ANY rule matches (OR logic).

        Args:
            resource_id: The resource identifier.
            level: Access level type.
            owner_email: Owner email for PRIVATE/DOMAIN levels.
            domain: Allowed domain for DOMAIN level.
            domains: Allowed domains for DOMAINS level.
            emails: Allowed emails for SPECIFIC level.
            groups: Allowed groups for GROUP level.
            roles: Allowed roles for ROLE level.
            metadata: Additional metadata.
        """
        if isinstance(level, str):
            level = AccessLevel(level)

        rule = AccessRule(
            resource_id=resource_id,
            level=level,
            owner_email=owner_email,
            domain=domain,
            domains=domains or [],
            emails=emails or [],
            groups=groups or [],
            roles=roles or [],
            metadata=metadata or {},
        )

        if resource_id not in self._rules:
            self._rules[resource_id] = []
        self._rules[resource_id].append(rule)

    def remove_rules(self, resource_id: str) -> None:
        """Remove all rules for a resource.

        Args:
            resource_id: The resource to remove rules for.
        """
        self._rules.pop(resource_id, None)

    def check_access(
        self,
        resource_id: str,
        user_email: Optional[str] = None,
        user_groups: Optional[Set[str]] = None,
        user_roles: Optional[Set[str]] = None,
    ) -> bool:
        """Check if a user has access to a resource.

        If no rules exist for the resource, access is granted by default
        (open access). If rules exist, at least one must match.

        Args:
            resource_id: Resource to check.
            user_email: User's email address.
            user_groups: User's group memberships.
            user_roles: User's roles.

        Returns:
            True if user has access.
        """
        rules = self._rules.get(resource_id)
        if not rules:
            return True  # No rules = open access

        return any(
            check_access(rule, user_email, user_groups, user_roles)
            for rule in rules
        )

    def filter_resources(
        self,
        resource_ids: List[str],
        user_email: Optional[str] = None,
        user_groups: Optional[Set[str]] = None,
        user_roles: Optional[Set[str]] = None,
    ) -> List[str]:
        """Filter a list of resources to those the user can access.

        Args:
            resource_ids: Resources to filter.
            user_email: User's email address.
            user_groups: User's group memberships.
            user_roles: User's roles.

        Returns:
            Filtered list of accessible resource IDs.
        """
        return [
            rid for rid in resource_ids
            if self.check_access(rid, user_email, user_groups, user_roles)
        ]

    def list_rules(self, resource_id: Optional[str] = None) -> List[AccessRule]:
        """List access rules.

        Args:
            resource_id: If provided, list rules for this resource only.
                If None, list all rules.

        Returns:
            List of AccessRule objects.
        """
        if resource_id:
            return list(self._rules.get(resource_id, []))
        return [
            rule
            for rules in self._rules.values()
            for rule in rules
        ]

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> AccessControl:
        """Create AccessControl from a configuration dict.

        Config format:
            {
                "resource_id": {
                    "level": "domain",
                    "domain": "company.com",
                    ...
                },
                "other_resource": [
                    {"level": "specific", "emails": ["a@b.com"]},
                    {"level": "domain", "domain": "c.com"},
                ],
            }

        Args:
            config: Configuration dictionary.

        Returns:
            Configured AccessControl instance.
        """
        ac = cls()
        for resource_id, rule_data in config.items():
            if isinstance(rule_data, dict):
                rule_data = [rule_data]
            if isinstance(rule_data, list):
                for rd in rule_data:
                    ac.add_rule(
                        resource_id=resource_id,
                        level=rd.get("level", "public"),
                        owner_email=rd.get("owner_email", ""),
                        domain=rd.get("domain", ""),
                        domains=rd.get("domains", []),
                        emails=rd.get("emails", []),
                        groups=rd.get("groups", []),
                        roles=rd.get("roles", []),
                        metadata=rd.get("metadata", {}),
                    )
        return ac
