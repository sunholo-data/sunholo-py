#!/usr/bin/env python3
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
ADK Agent Demo using sunholo.adk

Demonstrates how to use the sunholo ADK module to build and run
Google ADK agents with:
- SubAgentRegistry for agent factory registration
- ModelRegistry for multi-model support
- DynamicRunner for per-request agent execution
- ADK session and artifact services
- Event transformation for SSE streaming

Prerequisites:
    pip install sunholo[adk]

    # Set up your model access:
    export GOOGLE_API_KEY=your-key        # For Gemini models
    # OR
    export OPENAI_API_KEY=your-key        # For OpenAI via LiteLLM
    # OR
    export ANTHROPIC_API_KEY=your-key     # For Claude via LiteLLM

Usage:
    python examples/adk_agent_demo.py
"""
from __future__ import annotations

import asyncio
import sys


def check_dependencies():
    """Check that required dependencies are available."""
    missing = []
    try:
        import google.adk  # noqa: F401
    except ImportError:
        missing.append("google-adk")

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install sunholo[adk]")
        print("\nThis demo shows the API patterns - see code below for examples.")
        return False
    return True


def demo_sub_agent_registry():
    """Demonstrate SubAgentRegistry for managing agent factories."""
    from sunholo.adk.runner import SubAgentRegistry

    registry = SubAgentRegistry()

    # Register agent factories - functions that create agents on demand
    # In a real app, these would create google.adk.agents.Agent instances
    def create_search_agent():
        """Factory for a search agent."""
        print("  -> Would create search agent with web search tools")
        return "search_agent_instance"

    def create_email_agent():
        """Factory for an email agent."""
        print("  -> Would create email agent with email tools")
        return "email_agent_instance"

    # Register with capability descriptions
    registry.register(
        "search",
        factory=create_search_agent,
        capability="Search the web for information",
    )
    registry.register(
        "email",
        factory=create_email_agent,
        capability="Read and send emails",
        is_default=False,  # Optional agent, not included by default
    )

    print("Registered agents:")
    for agent_id, entry in registry.list_agents().items():
        print(f"  {agent_id}: {entry['capability']} (default={entry['is_default']})")

    print("\nDefault agents:", registry.get_default_ids())
    print("Optional agents:", registry.get_optional_ids())

    # Create agent instances
    print("\nCreating agents:")
    for agent_id in registry.list_agents():
        instance = registry.create(agent_id)
        print(f"  {agent_id} -> {instance}")


def demo_model_registry():
    """Demonstrate ModelRegistry for multi-model support."""
    from sunholo.adk.runner import ModelRegistry

    registry = ModelRegistry()

    # Register models with display names
    registry.register("gemini-2.0-flash", display_name="Gemini Flash")
    registry.register("gpt-4o", display_name="GPT-4o")
    registry.register("claude-sonnet-4-20250514", display_name="Claude Sonnet")

    print("Registered models:")
    for model_id in registry.list_models():
        info = registry.get_info(model_id)
        print(f"  {model_id} -> display: {info.get('display_name', 'N/A')}")

    # Unknown models can pass through
    print(f"\nUnknown model exists: {registry.get_info('unknown-model')}")


def demo_build_instruction():
    """Demonstrate instruction building from templates."""
    from sunholo.adk.runner import build_instruction

    template = (
        "You are a helpful assistant.\n"
        "Your name is {assistant_name}.\n"
        "You specialize in {specialty}.\n"
        "Today's date is {date}."
    )

    instruction = build_instruction(
        template=template,
        assistant_name="Demo Bot",
        specialty="answering questions about sunholo",
        date="2025-01-15",
    )

    print("Built instruction:")
    print(f"  {instruction[:100]}...")


def demo_event_transformer():
    """Demonstrate event transformation for SSE streaming."""
    from sunholo.adk.events import EventTransformer, ToolFeedback, FeedbackType

    transformer = EventTransformer()

    # Register a custom tool display name
    transformer.register_tool_display("web_search", display_name="Web Search")
    transformer.register_tool_display("email_send", display_name="Email Sender")

    # Create tool feedback events (these would come from ADK during execution)
    start_event = ToolFeedback(
        tool_name="web_search",
        feedback_type=FeedbackType.START,
        message="Searching for 'sunholo documentation'...",
    )

    complete_event = ToolFeedback(
        tool_name="web_search",
        feedback_type=FeedbackType.COMPLETE,
        message="Found 5 results",
        metadata={"result_count": 5},
    )

    print("Tool feedback events:")
    print(f"  Start: {start_event.to_dict()}")
    print(f"  Complete: {complete_event.to_dict()}")

    # Transform to SSE format
    sse_data = transformer.to_sse_event(start_event)
    print(f"\nSSE event: {sse_data}")


def demo_session_helper():
    """Demonstrate session helper for auth injection."""
    from sunholo.adk.session import SessionHelper, SessionKeys

    print("Session keys:")
    print(f"  User ID: {SessionKeys.USER_ID}")
    print(f"  Auth Token: {SessionKeys.AUTH_TOKEN}")
    print(f"  Config: {SessionKeys.CONFIG}")

    helper = SessionHelper()

    # Build session state with user context
    state = helper.build_session_state(
        user_id="user@example.com",
        auth_token="bearer_token_abc123",
        config={"model": "gemini-2.0-flash", "temperature": 0.7},
        extra={"custom_field": "custom_value"},
    )

    print(f"\nSession state keys: {list(state.keys())}")
    print(f"  User ID: {state.get(SessionKeys.USER_ID)}")


def demo_thinking_capture():
    """Demonstrate thinking content capture."""
    from sunholo.genai.thinking import ThinkingCapture, extract_thinking_simple

    # Extract thinking from a complete response
    response_text = (
        "<thinking>Let me analyze this question carefully. "
        "The user wants to know about sunholo.</thinking>"
        "Sunholo is a comprehensive toolkit for deploying GenAI applications."
    )

    thinking, cleaned = extract_thinking_simple(response_text)
    print("Extracted thinking:")
    print(f"  Thinking: {thinking[:60]}...")
    print(f"  Response: {cleaned[:60]}...")

    # Streaming capture
    print("\nStreaming capture:")
    capture = ThinkingCapture()
    chunks = [
        "Here is ",
        "my answer. <thin",
        "king>Let me think",
        " about this...</thi",
        "nking> The answer is 42.",
    ]

    for chunk in chunks:
        response = capture.process_chunk(chunk)
        if response:
            print(f"  Response chunk: '{response}'")

    remaining = capture.flush()
    if remaining:
        print(f"  Final chunk: '{remaining}'")

    print(f"  Total thinking: '{capture.get_thinking()}'")
    print(f"  Total response: '{capture.get_response()}'")


def demo_access_control():
    """Demonstrate access control system."""
    from sunholo.auth.access_control import AccessControl, AccessLevel

    ac = AccessControl()

    # Set up rules
    ac.add_rule("public-vac", AccessLevel.PUBLIC)
    ac.add_rule("internal-tools", AccessLevel.DOMAIN, domain="company.com")
    ac.add_rule("admin-panel", AccessLevel.SPECIFIC, emails=["admin@company.com"])
    ac.add_rule(
        "team-dashboard",
        AccessLevel.DOMAINS,
        domains=["company.com", "partner.com"],
    )

    # Check access for different users
    users = [
        "admin@company.com",
        "employee@company.com",
        "partner@partner.com",
        "external@gmail.com",
    ]

    resources = ["public-vac", "internal-tools", "admin-panel", "team-dashboard"]

    print("Access matrix:")
    header = f"{'User':<30}" + "".join(f"{r:<20}" for r in resources)
    print(f"  {header}")
    print(f"  {'-' * len(header)}")

    for user in users:
        checks = []
        for resource in resources:
            has_access = ac.check_access(resource, user_email=user)
            checks.append("YES" if has_access else "no")
        row = f"{user:<30}" + "".join(f"{c:<20}" for c in checks)
        print(f"  {row}")

    # Filter resources for a user
    allowed = ac.filter_resources(resources, user_email="employee@company.com")
    print(f"\nEmployee can access: {allowed}")


def demo_tool_permissions():
    """Demonstrate tool permissions system."""
    from sunholo.tools.permissions import permitted_tools, check_tag_permissions

    # Define permission rules
    rules = [
        {
            "domain": "company.com",
            "tools": ["search", "email", "calendar"],
            "toolConfigs": {
                "search": {"max_results": 20},
                "email": {"send_limit": 50},
            },
        },
        {
            "email": "admin@company.com",
            "tools": ["search", "email", "calendar", "admin", "analytics"],
            "toolConfigs": {
                "admin": {"can_delete": True},
            },
        },
    ]

    defaults = {
        "tools": ["search"],
        "toolConfigs": {"search": {"max_results": 10}},
    }

    # Check permissions for regular user
    user = {"email": "user@company.com"}
    allowed, configs = permitted_tools(
        current_user=user,
        requested_tools=["search", "email", "calendar", "admin"],
        permission_rules=rules,
        default_permissions=defaults,
        use_cache=False,
    )
    print(f"Regular user allowed tools: {allowed}")
    print(f"Regular user configs: {configs}")

    # Check permissions for admin
    admin = {"email": "admin@company.com"}
    allowed, configs = permitted_tools(
        current_user=admin,
        requested_tools=["search", "email", "calendar", "admin"],
        permission_rules=rules,
        default_permissions=defaults,
        use_cache=False,
    )
    print(f"\nAdmin allowed tools: {allowed}")
    print(f"Admin configs: {configs}")

    # Tag-based permissions
    tag_perms = {
        "internal": {"type": "domain", "domain": "company.com"},
        "public": {"type": "public"},
    }
    has_access = check_tag_permissions(
        "user@company.com", ["internal"], tag_perms, owner_email="owner@company.com"
    )
    print(f"\nInternal tag access for company user: {has_access}")


def main():
    """Run all demos."""
    print("=" * 60)
    print("Sunholo ADK Agent Demo")
    print("=" * 60)

    demos = [
        ("SubAgent Registry", demo_sub_agent_registry),
        ("Model Registry", demo_model_registry),
        ("Instruction Building", demo_build_instruction),
        ("Event Transformer", demo_event_transformer),
        ("Session Helper", demo_session_helper),
        ("Thinking Capture", demo_thinking_capture),
        ("Access Control", demo_access_control),
        ("Tool Permissions", demo_tool_permissions),
    ]

    for name, demo_fn in demos:
        print(f"\n{'─' * 60}")
        print(f"Demo: {name}")
        print(f"{'─' * 60}")
        try:
            demo_fn()
        except ImportError as e:
            print(f"  Skipped (missing dependency): {e}")
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\n{'=' * 60}")
    print("Demo complete!")

    if not check_dependencies():
        print("\nNote: Install google-adk for full ADK features.")
        print("The patterns above work without ADK installed.")


if __name__ == "__main__":
    main()
