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
Config-driven tool permission system.

Provides security-critical permission validation for tool access based on
user email/domain matching. Supports:
- Email-exact and domain-level matching
- Wildcard config parameters (user-provided values)
- Time-based caching with TTL
- Batch permission checking
- Tag-based access control

Usage:
    from sunholo.tools.permissions import permitted_tools, PermissionCache

    # Check permissions for a user
    allowed_tools, configs = permitted_tools(
        current_user={"email": "user@company.com"},
        requested_tools=["search", "email", "calendar"],
        permission_rules=rules,
        default_permissions=defaults,
    )

    # Tag-based access
    has_access = check_tag_permissions(
        user_email="user@company.com",
        tags=["internal"],
        tag_permissions={"internal": {"type": "domain", "domain": "company.com"}},
    )
"""
from __future__ import annotations

import copy
import hashlib
import logging
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class PermissionCache:
    """Time-based cache for permission results.

    Prevents redundant permission computation for repeated requests
    within the TTL window.

    Args:
        max_size: Maximum cache entries.
        ttl_seconds: Time-to-live for cache entries in seconds.
    """

    def __init__(self, max_size: int = 500, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}

    def _is_expired(self, key: str) -> bool:
        ts = self._timestamps.get(key)
        if ts is None:
            return True
        return (time.time() - ts) > self.ttl_seconds

    def _cleanup_expired(self) -> None:
        expired = [k for k in self._timestamps if self._is_expired(k)]
        for k in expired:
            self._cache.pop(k, None)
            self._timestamps.pop(k, None)

    def get(self, key: str) -> Any:
        """Get cached value, or None if expired/missing."""
        if key in self._cache and not self._is_expired(key):
            return self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a cached value with current timestamp."""
        if len(self._cache) >= self.max_size:
            self._cleanup_expired()
            if len(self._cache) >= self.max_size:
                oldest = min(self._timestamps, key=self._timestamps.get)
                self._cache.pop(oldest, None)
                self._timestamps.pop(oldest, None)
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._timestamps.clear()


# Module-level cache
_permission_cache = PermissionCache()


@lru_cache(maxsize=1000)
def is_matching_email_or_domain(user_email: str, pattern: str) -> bool:
    """Check if a user email matches an email or domain pattern.

    Args:
        user_email: User's email address (case-insensitive).
        pattern: Email address or domain pattern to match against.

    Returns:
        True if the user matches the pattern.
    """
    email_lower = user_email.lower()
    pattern_lower = pattern.lower()

    # Exact email match
    if email_lower == pattern_lower:
        return True

    # Domain-only match (pattern is just a domain like "company.com")
    if "@" not in pattern_lower and email_lower.endswith(f"@{pattern_lower}"):
        return True

    return False


def create_permission_cache_key(
    user_email: str,
    tools: List[str],
    config: Dict[str, Any] | None = None,
    vac_name: str = "",
) -> str:
    """Create a stable cache key from permission request parameters.

    Args:
        user_email: User email.
        tools: Requested tools list.
        config: Tool configs dict.
        vac_name: VAC name.

    Returns:
        MD5 hash string.
    """
    parts = [
        user_email.lower(),
        ",".join(sorted(tools)),
        str(sorted((config or {}).items())),
        vac_name,
    ]
    raw = "|".join(parts)
    return hashlib.md5(raw.encode()).hexdigest()


def permitted_tools(
    current_user: Optional[Dict[str, str]],
    requested_tools: List[str],
    permission_rules: List[Dict[str, Any]] | None = None,
    default_permissions: Dict[str, Any] | None = None,
    tool_configs: Optional[Dict[str, Any]] = None,
    vac_name: str = "",
    use_cache: bool = True,
) -> Tuple[List[str], Dict[str, Any]]:
    """Validate and filter tools based on user permissions.

    Performs security-critical permission validation:
    1. Checks user email against permission rules
    2. Filters requested tools to allowed set
    3. Merges user-provided configs with defaults
    4. Handles wildcard ("*") config values

    Args:
        current_user: Dict with "email" key, or None for anonymous.
        requested_tools: List of tool IDs the user wants to use.
        permission_rules: List of permission rule dicts, each with:
            - "email" or "domain": Pattern to match
            - "tools": List of allowed tool IDs
            - "toolConfigs": Dict of tool-specific configs
        default_permissions: Default permissions dict with:
            - "tools": Default allowed tools
            - "toolConfigs": Default tool configs
        tool_configs: User-provided tool configs (overrides defaults
            where wildcard "*" values are present).
        vac_name: VAC name for cache key generation.
        use_cache: Whether to use permission cache.

    Returns:
        Tuple of (filtered_tools, merged_configs).
        - filtered_tools: Only tools the user is allowed to use
        - merged_configs: Tool configs with user values applied to wildcards
    """
    user_email = ""
    if current_user:
        user_email = current_user.get("email", "").lower()

    # Check cache
    if use_cache and user_email:
        cache_key = create_permission_cache_key(
            user_email, requested_tools, tool_configs, vac_name
        )
        cached = _permission_cache.get(cache_key)
        if cached is not None:
            return cached

    # Start with defaults
    defaults = default_permissions or {}
    allowed_tools: Set[str] = set(defaults.get("tools", []))
    result_configs: Dict[str, Any] = copy.deepcopy(defaults.get("toolConfigs", {}))

    # Apply permission rules
    if permission_rules and user_email:
        for rule in permission_rules:
            # Check email match
            rule_email = rule.get("email", "")
            rule_domain = rule.get("domain", "")
            pattern = rule_email or rule_domain

            if not pattern:
                continue

            if is_matching_email_or_domain(user_email, pattern):
                # Add tools from this rule
                rule_tools = rule.get("tools", [])
                if rule_tools:
                    allowed_tools.update(rule_tools)

                # Merge tool configs from this rule
                rule_configs = rule.get("toolConfigs", {})
                for tool_name, config in rule_configs.items():
                    if tool_name not in result_configs:
                        result_configs[tool_name] = {}
                    result_configs[tool_name].update(config)

    # Filter requested tools to allowed set
    if allowed_tools:
        filtered = [t for t in requested_tools if t in allowed_tools]
    else:
        # No rules matched and no defaults - allow all requested
        filtered = list(requested_tools)

    # Apply user-provided config values to wildcard entries
    if tool_configs:
        for tool_name, user_config in tool_configs.items():
            if tool_name not in result_configs:
                result_configs[tool_name] = {}
            for key, value in user_config.items():
                # Only apply if default is wildcard ("*") or not set
                default_val = result_configs[tool_name].get(key)
                if default_val == "*" or default_val is None:
                    result_configs[tool_name][key] = value

    result = (filtered, result_configs)

    # Cache result
    if use_cache and user_email:
        _permission_cache.set(cache_key, result)

    return result


def batch_permitted_tools(
    requests: List[Tuple[Optional[Dict[str, str]], List[str], Optional[Dict], str]],
    permission_rules: List[Dict[str, Any]] | None = None,
    default_permissions: Dict[str, Any] | None = None,
) -> List[Tuple[List[str], Dict[str, Any]]]:
    """Process multiple permission requests efficiently.

    Groups requests to minimize redundant config loading.

    Args:
        requests: List of (current_user, requested_tools, tool_configs, vac_name).
        permission_rules: Shared permission rules.
        default_permissions: Shared default permissions.

    Returns:
        List of (filtered_tools, merged_configs) results.
    """
    return [
        permitted_tools(
            current_user=user,
            requested_tools=tools,
            permission_rules=permission_rules,
            default_permissions=default_permissions,
            tool_configs=configs,
            vac_name=vac,
        )
        for user, tools, configs, vac in requests
    ]


def extract_domain(email: str) -> Optional[str]:
    """Extract domain from an email address.

    Args:
        email: Email address string.

    Returns:
        Lowercase domain, or None if invalid.
    """
    if not email or "@" not in email:
        return None
    return email.lower().split("@")[1]


def check_tag_permissions(
    user_email: Optional[str],
    tags: List[str],
    tag_permissions: Dict[str, Dict[str, Any]],
    owner_email: str = "",
) -> bool:
    """Check if a user has permission to access resources with given tags.

    Access types:
    - "public": Anyone can access
    - "private": Only owner
    - "domain": Same domain as owner
    - "domains": User's domain in allowed list
    - "specific": User's email in allowed list
    - "group": User in allowed groups

    Args:
        user_email: User's email (None for anonymous).
        tags: Tags on the resource.
        tag_permissions: Permission rules per tag.
        owner_email: Resource owner's email.

    Returns:
        True if user has access to at least one tag.
    """
    if not tags:
        return True  # No tags = no restrictions

    email = (user_email or "").lower()

    for tag in tags:
        perms = tag_permissions.get(tag)
        if not perms:
            continue  # No permissions for this tag = open access

        access_type = perms.get("type", "public")

        if access_type == "public":
            return True

        if not email:
            continue  # Anonymous users can't pass non-public checks

        if access_type == "private":
            if email == owner_email.lower():
                return True

        elif access_type == "domain":
            owner_domain = extract_domain(owner_email)
            user_domain = extract_domain(email)
            if owner_domain and user_domain and owner_domain == user_domain:
                return True

        elif access_type == "domains":
            allowed_domains = [d.lower() for d in perms.get("domains", [])]
            user_domain = extract_domain(email)
            if user_domain and user_domain in allowed_domains:
                return True

        elif access_type == "specific":
            allowed_emails = [e.lower() for e in perms.get("emails", [])]
            if email in allowed_emails:
                return True

        elif access_type == "group":
            # Group checking requires external group resolution
            allowed_groups = perms.get("groups", [])
            logger.debug("Group permission check not yet implemented for groups: %s", allowed_groups)

    return False


def filter_tools_by_tags(
    user_email: Optional[str],
    requested_tools: List[str],
    tool_tags: Dict[str, List[str]],
    tag_permissions: Dict[str, Dict[str, Any]],
    owner_email: str = "",
) -> List[str]:
    """Filter tools based on tag-level permissions.

    Args:
        user_email: User's email.
        requested_tools: Tools the user wants to use.
        tool_tags: Mapping of tool_id -> list of tags.
        tag_permissions: Permission rules per tag.
        owner_email: Owner email for private/domain checks.

    Returns:
        Filtered list of tools the user can access.
    """
    result = []
    for tool in requested_tools:
        tags = tool_tags.get(tool, [])
        if check_tag_permissions(user_email, tags, tag_permissions, owner_email):
            result.append(tool)
    return result
