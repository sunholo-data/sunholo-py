"""Tests for sunholo.auth.access_control module."""
import pytest

from sunholo.auth.access_control import (
    AccessControl,
    AccessLevel,
    AccessRule,
    check_access,
    extract_domain,
)


class TestAccessLevel:
    def test_enum_values(self):
        assert AccessLevel.PUBLIC == "public"
        assert AccessLevel.PRIVATE == "private"
        assert AccessLevel.DOMAIN == "domain"
        assert AccessLevel.DOMAINS == "domains"
        assert AccessLevel.SPECIFIC == "specific"
        assert AccessLevel.GROUP == "group"
        assert AccessLevel.ROLE == "role"

    def test_from_string(self):
        assert AccessLevel("public") == AccessLevel.PUBLIC
        assert AccessLevel("domain") == AccessLevel.DOMAIN


class TestExtractDomain:
    def test_valid(self):
        assert extract_domain("user@company.com") == "company.com"

    def test_uppercase(self):
        assert extract_domain("User@COMPANY.COM") == "company.com"

    def test_no_at(self):
        assert extract_domain("noemail") is None

    def test_empty(self):
        assert extract_domain("") is None


class TestCheckAccess:
    def test_public_always_grants(self):
        rule = AccessRule(resource_id="r1", level=AccessLevel.PUBLIC)
        assert check_access(rule)
        assert check_access(rule, user_email="anyone@a.com")
        assert check_access(rule, user_email=None)

    def test_private_owner_only(self):
        rule = AccessRule(
            resource_id="r1",
            level=AccessLevel.PRIVATE,
            owner_email="owner@a.com",
        )
        assert check_access(rule, user_email="owner@a.com")
        assert not check_access(rule, user_email="other@a.com")
        assert not check_access(rule)

    def test_private_case_insensitive(self):
        rule = AccessRule(
            resource_id="r1",
            level=AccessLevel.PRIVATE,
            owner_email="Owner@A.com",
        )
        assert check_access(rule, user_email="owner@a.com")

    def test_domain_with_explicit_domain(self):
        rule = AccessRule(
            resource_id="r1",
            level=AccessLevel.DOMAIN,
            domain="company.com",
        )
        assert check_access(rule, user_email="user@company.com")
        assert not check_access(rule, user_email="user@other.com")

    def test_domain_from_owner(self):
        rule = AccessRule(
            resource_id="r1",
            level=AccessLevel.DOMAIN,
            owner_email="owner@company.com",
        )
        assert check_access(rule, user_email="colleague@company.com")
        assert not check_access(rule, user_email="user@other.com")

    def test_domains_list(self):
        rule = AccessRule(
            resource_id="r1",
            level=AccessLevel.DOMAINS,
            domains=["a.com", "b.com"],
        )
        assert check_access(rule, user_email="user@a.com")
        assert check_access(rule, user_email="user@b.com")
        assert not check_access(rule, user_email="user@c.com")

    def test_specific_emails(self):
        rule = AccessRule(
            resource_id="r1",
            level=AccessLevel.SPECIFIC,
            emails=["alice@a.com", "bob@b.com"],
        )
        assert check_access(rule, user_email="alice@a.com")
        assert check_access(rule, user_email="Bob@B.com")
        assert not check_access(rule, user_email="charlie@a.com")

    def test_group_access(self):
        rule = AccessRule(
            resource_id="r1",
            level=AccessLevel.GROUP,
            groups=["admins", "editors"],
        )
        assert check_access(rule, user_groups={"admins"})
        assert check_access(rule, user_groups={"editors", "viewers"})
        assert not check_access(rule, user_groups={"viewers"})
        assert not check_access(rule)

    def test_role_access(self):
        rule = AccessRule(
            resource_id="r1",
            level=AccessLevel.ROLE,
            roles=["admin", "superuser"],
        )
        assert check_access(rule, user_roles={"admin"})
        assert not check_access(rule, user_roles={"viewer"})
        assert not check_access(rule)

    def test_anonymous_fails_non_public(self):
        for level in [AccessLevel.PRIVATE, AccessLevel.DOMAIN, AccessLevel.SPECIFIC]:
            rule = AccessRule(resource_id="r1", level=level, owner_email="o@a.com")
            assert not check_access(rule)


class TestAccessControl:
    def test_no_rules_grants_access(self):
        ac = AccessControl()
        assert ac.check_access("any-resource", user_email="user@a.com")

    def test_add_and_check_rule(self):
        ac = AccessControl()
        ac.add_rule("my-vac", AccessLevel.DOMAIN, domain="company.com")
        assert ac.check_access("my-vac", user_email="user@company.com")
        assert not ac.check_access("my-vac", user_email="user@other.com")

    def test_multiple_rules_or_logic(self):
        ac = AccessControl()
        ac.add_rule("resource", AccessLevel.SPECIFIC, emails=["a@x.com"])
        ac.add_rule("resource", AccessLevel.DOMAIN, domain="y.com")
        assert ac.check_access("resource", user_email="a@x.com")
        assert ac.check_access("resource", user_email="b@y.com")
        assert not ac.check_access("resource", user_email="c@z.com")

    def test_remove_rules(self):
        ac = AccessControl()
        ac.add_rule("resource", AccessLevel.SPECIFIC, emails=["a@x.com"])
        assert ac.check_access("resource", user_email="a@x.com")
        ac.remove_rules("resource")
        # No rules = open access
        assert ac.check_access("resource", user_email="anyone@z.com")

    def test_filter_resources(self):
        ac = AccessControl()
        ac.add_rule("public", AccessLevel.PUBLIC)
        ac.add_rule("internal", AccessLevel.DOMAIN, domain="company.com")
        ac.add_rule("admin", AccessLevel.SPECIFIC, emails=["admin@company.com"])

        result = ac.filter_resources(
            ["public", "internal", "admin"],
            user_email="user@company.com",
        )
        assert "public" in result
        assert "internal" in result
        assert "admin" not in result

    def test_filter_resources_admin(self):
        ac = AccessControl()
        ac.add_rule("internal", AccessLevel.DOMAIN, domain="company.com")
        ac.add_rule("admin", AccessLevel.SPECIFIC, emails=["admin@company.com"])

        result = ac.filter_resources(
            ["internal", "admin"],
            user_email="admin@company.com",
        )
        assert "internal" in result
        assert "admin" in result

    def test_list_rules(self):
        ac = AccessControl()
        ac.add_rule("r1", AccessLevel.PUBLIC)
        ac.add_rule("r2", AccessLevel.DOMAIN, domain="a.com")
        rules = ac.list_rules()
        assert len(rules) == 2

    def test_list_rules_for_resource(self):
        ac = AccessControl()
        ac.add_rule("r1", AccessLevel.PUBLIC)
        ac.add_rule("r1", AccessLevel.DOMAIN, domain="a.com")
        ac.add_rule("r2", AccessLevel.SPECIFIC, emails=["x@y.com"])
        rules = ac.list_rules("r1")
        assert len(rules) == 2

    def test_add_rule_string_level(self):
        ac = AccessControl()
        ac.add_rule("r1", "public")
        assert ac.check_access("r1")

    def test_from_config_single_rule(self):
        config = {
            "my-vac": {"level": "domain", "domain": "company.com"},
        }
        ac = AccessControl.from_config(config)
        assert ac.check_access("my-vac", user_email="user@company.com")
        assert not ac.check_access("my-vac", user_email="user@other.com")

    def test_from_config_multiple_rules(self):
        config = {
            "resource": [
                {"level": "specific", "emails": ["a@x.com"]},
                {"level": "domain", "domain": "y.com"},
            ],
        }
        ac = AccessControl.from_config(config)
        assert ac.check_access("resource", user_email="a@x.com")
        assert ac.check_access("resource", user_email="b@y.com")
        assert not ac.check_access("resource", user_email="c@z.com")

    def test_group_and_role(self):
        ac = AccessControl()
        ac.add_rule("admin-tools", AccessLevel.GROUP, groups=["admins"])
        ac.add_rule("superuser-tools", AccessLevel.ROLE, roles=["superuser"])

        assert ac.check_access("admin-tools", user_groups={"admins"})
        assert not ac.check_access("admin-tools", user_groups={"viewers"})
        assert ac.check_access("superuser-tools", user_roles={"superuser"})
        assert not ac.check_access("superuser-tools", user_roles={"viewer"})
