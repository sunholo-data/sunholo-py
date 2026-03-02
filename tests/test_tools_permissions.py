"""Tests for sunholo.tools.permissions module."""
import pytest
import time

from sunholo.tools.permissions import (
    PermissionCache,
    is_matching_email_or_domain,
    create_permission_cache_key,
    permitted_tools,
    batch_permitted_tools,
    extract_domain,
    check_tag_permissions,
    filter_tools_by_tags,
)


class TestPermissionCache:
    def test_set_and_get(self):
        cache = PermissionCache(max_size=10, ttl_seconds=300)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_missing_key_returns_none(self):
        cache = PermissionCache()
        assert cache.get("nonexistent") is None

    def test_expired_entry_returns_none(self):
        cache = PermissionCache(ttl_seconds=0)
        cache.set("key1", "value1")
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_clear(self):
        cache = PermissionCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_max_size_eviction(self):
        cache = PermissionCache(max_size=2, ttl_seconds=300)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # Should evict oldest
        assert cache.get("c") == 3
        # One of a or b should be evicted
        remaining = [cache.get("a"), cache.get("b")]
        assert None in remaining


class TestEmailMatching:
    def test_exact_email_match(self):
        assert is_matching_email_or_domain("user@company.com", "user@company.com")

    def test_case_insensitive_email(self):
        assert is_matching_email_or_domain("User@Company.COM", "user@company.com")

    def test_domain_match(self):
        assert is_matching_email_or_domain("anyone@company.com", "company.com")

    def test_domain_no_match(self):
        assert not is_matching_email_or_domain("user@other.com", "company.com")

    def test_different_email_no_match(self):
        assert not is_matching_email_or_domain("user@a.com", "admin@a.com")


class TestCacheKey:
    def test_consistent_key(self):
        key1 = create_permission_cache_key("user@a.com", ["tool1", "tool2"])
        key2 = create_permission_cache_key("user@a.com", ["tool1", "tool2"])
        assert key1 == key2

    def test_different_tools_different_key(self):
        key1 = create_permission_cache_key("user@a.com", ["tool1"])
        key2 = create_permission_cache_key("user@a.com", ["tool2"])
        assert key1 != key2

    def test_case_insensitive_email(self):
        key1 = create_permission_cache_key("User@A.com", ["tool1"])
        key2 = create_permission_cache_key("user@a.com", ["tool1"])
        assert key1 == key2


class TestPermittedTools:
    def test_no_rules_allows_all(self):
        tools, configs = permitted_tools(
            current_user={"email": "user@a.com"},
            requested_tools=["search", "email"],
            use_cache=False,
        )
        assert tools == ["search", "email"]

    def test_default_permissions(self):
        defaults = {"tools": ["search", "calc"], "toolConfigs": {}}
        tools, _ = permitted_tools(
            current_user={"email": "user@a.com"},
            requested_tools=["search", "email", "calc"],
            default_permissions=defaults,
            use_cache=False,
        )
        assert "search" in tools
        assert "calc" in tools
        assert "email" not in tools

    def test_rule_adds_tools(self):
        rules = [
            {"domain": "company.com", "tools": ["search", "email"]}
        ]
        defaults = {"tools": ["search"], "toolConfigs": {}}
        tools, _ = permitted_tools(
            current_user={"email": "user@company.com"},
            requested_tools=["search", "email", "admin"],
            permission_rules=rules,
            default_permissions=defaults,
            use_cache=False,
        )
        assert "search" in tools
        assert "email" in tools
        assert "admin" not in tools

    def test_wildcard_config_override(self):
        defaults = {
            "tools": ["search"],
            "toolConfigs": {"search": {"query": "*"}},
        }
        tools, configs = permitted_tools(
            current_user={"email": "user@a.com"},
            requested_tools=["search"],
            default_permissions=defaults,
            tool_configs={"search": {"query": "test query"}},
            use_cache=False,
        )
        assert configs["search"]["query"] == "test query"

    def test_non_wildcard_not_overridden(self):
        defaults = {
            "tools": ["search"],
            "toolConfigs": {"search": {"max_results": 10}},
        }
        tools, configs = permitted_tools(
            current_user={"email": "user@a.com"},
            requested_tools=["search"],
            default_permissions=defaults,
            tool_configs={"search": {"max_results": 99}},
            use_cache=False,
        )
        # Non-wildcard default should NOT be overridden
        assert configs["search"]["max_results"] == 10

    def test_anonymous_user(self):
        defaults = {"tools": ["search"], "toolConfigs": {}}
        tools, _ = permitted_tools(
            current_user=None,
            requested_tools=["search"],
            default_permissions=defaults,
            use_cache=False,
        )
        assert tools == ["search"]

    def test_caching(self):
        defaults = {"tools": ["search"], "toolConfigs": {}}
        # First call
        tools1, _ = permitted_tools(
            current_user={"email": "user@a.com"},
            requested_tools=["search"],
            default_permissions=defaults,
            use_cache=True,
        )
        # Second call should use cache
        tools2, _ = permitted_tools(
            current_user={"email": "user@a.com"},
            requested_tools=["search"],
            default_permissions=defaults,
            use_cache=True,
        )
        assert tools1 == tools2


class TestBatchPermittedTools:
    def test_batch_processing(self):
        defaults = {"tools": ["search", "email"], "toolConfigs": {}}
        requests = [
            ({"email": "user1@a.com"}, ["search", "email"], None, "vac1"),
            ({"email": "user2@a.com"}, ["search"], None, "vac2"),
        ]
        results = batch_permitted_tools(
            requests, default_permissions=defaults
        )
        assert len(results) == 2
        assert "search" in results[0][0]
        assert "search" in results[1][0]


class TestExtractDomain:
    def test_valid_email(self):
        assert extract_domain("user@company.com") == "company.com"

    def test_uppercase(self):
        assert extract_domain("User@COMPANY.COM") == "company.com"

    def test_no_at_sign(self):
        assert extract_domain("not_an_email") is None

    def test_empty(self):
        assert extract_domain("") is None


class TestTagPermissions:
    def test_no_tags_allows(self):
        assert check_tag_permissions("user@a.com", [], {})

    def test_public_tag(self):
        perms = {"public_tag": {"type": "public"}}
        assert check_tag_permissions("user@a.com", ["public_tag"], perms)
        assert check_tag_permissions(None, ["public_tag"], perms)

    def test_private_tag(self):
        perms = {"priv": {"type": "private"}}
        assert check_tag_permissions(
            "owner@a.com", ["priv"], perms, owner_email="owner@a.com"
        )
        assert not check_tag_permissions(
            "other@a.com", ["priv"], perms, owner_email="owner@a.com"
        )

    def test_domain_tag(self):
        perms = {"internal": {"type": "domain"}}
        assert check_tag_permissions(
            "user@company.com", ["internal"], perms, owner_email="owner@company.com"
        )
        assert not check_tag_permissions(
            "user@other.com", ["internal"], perms, owner_email="owner@company.com"
        )

    def test_domains_tag(self):
        perms = {"partners": {"type": "domains", "domains": ["a.com", "b.com"]}}
        assert check_tag_permissions("user@a.com", ["partners"], perms)
        assert check_tag_permissions("user@b.com", ["partners"], perms)
        assert not check_tag_permissions("user@c.com", ["partners"], perms)

    def test_specific_tag(self):
        perms = {"vip": {"type": "specific", "emails": ["vip@a.com", "boss@a.com"]}}
        assert check_tag_permissions("vip@a.com", ["vip"], perms)
        assert not check_tag_permissions("nobody@a.com", ["vip"], perms)

    def test_anonymous_non_public(self):
        perms = {"internal": {"type": "domain"}}
        assert not check_tag_permissions(None, ["internal"], perms, owner_email="o@a.com")

    def test_unknown_tag_denies(self):
        # Tags present but none have matching permission rules = denied
        assert not check_tag_permissions("user@a.com", ["unknown"], {})


class TestFilterToolsByTags:
    def test_filter(self):
        tool_tags = {
            "search": ["public"],
            "admin": ["internal"],
            "email": [],
        }
        tag_perms = {
            "public": {"type": "public"},
            "internal": {"type": "domain"},
        }
        result = filter_tools_by_tags(
            "user@other.com",
            ["search", "admin", "email"],
            tool_tags,
            tag_perms,
            owner_email="owner@company.com",
        )
        assert "search" in result
        assert "email" in result  # No tags = no restrictions
        assert "admin" not in result  # Different domain
