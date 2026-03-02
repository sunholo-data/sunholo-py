"""Tests for sunholo.adk module.

These tests verify the generalized ADK utilities without requiring
google-adk to be installed (using mocks where needed).
"""
import pytest
from unittest.mock import MagicMock, patch


class TestSubAgentRegistry:
    def test_register_default_tool(self):
        from sunholo.adk.runner import SubAgentRegistry
        registry = SubAgentRegistry()
        factory = MagicMock(return_value=MagicMock(name="search"))
        registry.register(
            "search",
            factory=factory,
            capability="Web search",
            delegation="search_agent for web queries",
            default=True,
        )
        assert "search" in registry.default_tools
        assert "search" not in registry.optional_tools

    def test_register_optional_tool(self):
        from sunholo.adk.runner import SubAgentRegistry
        registry = SubAgentRegistry()
        factory = MagicMock(return_value=MagicMock(name="email"))
        registry.register(
            "email",
            factory=factory,
            capability="Email search",
            default=False,
        )
        assert "email" in registry.optional_tools
        assert "email" not in registry.default_tools

    def test_get_filtered_agents(self):
        from sunholo.adk.runner import SubAgentRegistry
        registry = SubAgentRegistry()

        mock_agent_a = MagicMock(name="agent_a")
        mock_agent_b = MagicMock(name="agent_b")
        mock_agent_c = MagicMock(name="agent_c")

        registry.register("tool_a", factory=lambda: mock_agent_a, default=True)
        registry.register("tool_b", factory=lambda: mock_agent_b, default=False)
        registry.register("tool_c", factory=lambda: mock_agent_c, default=False)

        agents = registry.get_filtered_agents(["tool_a", "tool_b"])
        assert len(agents) == 2

    def test_always_included_agents(self):
        from sunholo.adk.runner import SubAgentRegistry
        registry = SubAgentRegistry()

        mock_always = MagicMock(name="always_agent")
        registry.register_always_included(lambda: mock_always)

        agents = registry.get_filtered_agents([])
        assert len(agents) == 1

    def test_duplicate_factory_deduplication(self):
        from sunholo.adk.runner import SubAgentRegistry
        registry = SubAgentRegistry()

        # Same factory for multiple tools (like MSN agent for sharepoint/email/calendar)
        shared_factory = lambda: MagicMock(name="shared")
        registry.register("sharepoint", factory=shared_factory)
        registry.register("email", factory=shared_factory)
        registry.register("calendar", factory=shared_factory)

        agents = registry.get_filtered_agents(["sharepoint", "email", "calendar"])
        # Should only create one agent since same factory
        assert len(agents) == 1

    def test_build_capabilities_text(self):
        from sunholo.adk.runner import SubAgentRegistry
        registry = SubAgentRegistry()
        registry.register("search", factory=lambda: None, capability="**Web Search**: Search the web")
        registry.register("code", factory=lambda: None, capability="**Code**: Run Python code")

        text = registry.build_capabilities_text(["search", "code"])
        assert "Web Search" in text
        assert "Code" in text

    def test_build_delegations_text(self):
        from sunholo.adk.runner import SubAgentRegistry
        registry = SubAgentRegistry()
        registry.register(
            "search", factory=lambda: None,
            delegation="search_agent for web queries",
        )

        text = registry.build_delegations_text(["search"])
        assert "search_agent" in text

    def test_get_disabled_descriptions(self):
        from sunholo.adk.runner import SubAgentRegistry
        registry = SubAgentRegistry()
        registry.register("search", factory=lambda: None, capability="Web Search", default=False)
        registry.register("email", factory=lambda: None, capability="Email", default=False)

        disabled = registry.get_disabled_descriptions(["search"])
        assert len(disabled) == 1
        assert "Email" in disabled[0]


class TestModelRegistry:
    def test_passthrough_gemini(self):
        from sunholo.adk.runner import ModelRegistry
        models = ModelRegistry(default_model="gemini-2.5-flash")
        result = models.get("gemini-2.5-pro")
        assert result == "gemini-2.5-pro"

    def test_registered_factory(self):
        from sunholo.adk.runner import ModelRegistry
        models = ModelRegistry()
        mock_model = MagicMock()
        models.register("gpt-4o", factory=lambda: mock_model)
        result = models.get("gpt-4o")
        assert result is mock_model

    def test_cached_model(self):
        from sunholo.adk.runner import ModelRegistry
        models = ModelRegistry()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return MagicMock()

        models.register("test-model", factory=factory)
        models.get("test-model")
        models.get("test-model")
        assert call_count == 1  # Factory should only be called once

    def test_fallback_to_default(self):
        from sunholo.adk.runner import ModelRegistry
        models = ModelRegistry(default_model="gemini-2.5-flash")
        result = models.get("unknown-model")
        assert result == "gemini-2.5-flash"

    def test_custom_passthrough_prefix(self):
        from sunholo.adk.runner import ModelRegistry
        models = ModelRegistry()
        models.add_passthrough_prefix("claude")
        result = models.get("claude-sonnet-4")
        assert result == "claude-sonnet-4"


class TestBuildInstruction:
    def test_basic_instruction(self):
        from sunholo.adk.runner import SubAgentRegistry, build_instruction
        registry = SubAgentRegistry()
        registry.register("search", factory=lambda: None, capability="Web search")

        instruction = build_instruction(
            registry=registry,
            enabled_tools=["search"],
        )
        assert "Web search" in instruction

    def test_custom_instruction(self):
        from sunholo.adk.runner import SubAgentRegistry, build_instruction
        registry = SubAgentRegistry()

        instruction = build_instruction(
            registry=registry,
            enabled_tools=[],
            custom_instruction="Focus on HR documents",
        )
        assert "HR documents" in instruction

    def test_template_variables(self):
        from sunholo.adk.runner import SubAgentRegistry, build_instruction
        registry = SubAgentRegistry()

        instruction = build_instruction(
            registry=registry,
            enabled_tools=[],
            base_instruction="Hello {name}, you are in {location}.",
            context_vars={"name": "Assistant", "location": "London"},
        )
        assert "Hello Assistant" in instruction
        assert "London" in instruction


class TestLiteLLMCompat:
    def test_generate_tool_call_id(self):
        from sunholo.adk.litellm_compat import generate_tool_call_id
        id1 = generate_tool_call_id()
        id2 = generate_tool_call_id()
        assert id1.startswith("call_")
        assert len(id1) == 29  # "call_" + 24 hex chars
        assert id1 != id2

    def test_is_text_mime_type(self):
        from sunholo.adk.litellm_compat import is_text_mime_type
        assert is_text_mime_type("text/plain")
        assert is_text_mime_type("text/html")
        assert is_text_mime_type("text/csv")
        assert is_text_mime_type("application/json")
        assert is_text_mime_type("application/xml")
        assert not is_text_mime_type("image/png")
        assert not is_text_mime_type("application/pdf")
        assert not is_text_mime_type("video/mp4")

    def test_fix_null_tool_call_ids_dict_messages(self):
        from sunholo.adk.litellm_compat import fix_null_tool_call_ids
        messages = [
            {
                "role": "assistant",
                "tool_calls": [
                    {"id": None, "function": {"name": "search", "arguments": "{}"}},
                    {"id": "call_existing", "function": {"name": "calc", "arguments": "{}"}},
                ],
            },
            {"role": "user", "content": "hello"},
        ]

        result = fix_null_tool_call_ids(messages)
        assert result[0]["tool_calls"][0]["id"] is not None
        assert result[0]["tool_calls"][0]["id"].startswith("call_")
        assert result[0]["tool_calls"][1]["id"] == "call_existing"

    def test_fix_null_tool_call_ids_pydantic_messages(self):
        from sunholo.adk.litellm_compat import fix_null_tool_call_ids

        class MockToolCall:
            def __init__(self, id=None):
                self.id = id
                self.function = MagicMock(name="test_func")

        class MockMessage:
            def __init__(self):
                self.role = "assistant"
                self.tool_calls = [MockToolCall(id=None), MockToolCall(id="existing")]

        messages = [MockMessage()]
        result = fix_null_tool_call_ids(messages)
        assert result[0].tool_calls[0].id is not None
        assert result[0].tool_calls[0].id.startswith("call_")
        assert result[0].tool_calls[1].id == "existing"

    def test_fix_no_tool_calls(self):
        from sunholo.adk.litellm_compat import fix_null_tool_call_ids
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        result = fix_null_tool_call_ids(messages)
        assert len(result) == 2


class TestEventTransformer:
    def test_tool_feedback_start(self):
        from sunholo.adk.events import ToolFeedback, FeedbackType
        feedback = ToolFeedback.start("search_tool", message="Searching documents...")
        assert feedback.tool_name == "search_tool"
        assert feedback.feedback_type == FeedbackType.START
        assert feedback.message == "Searching documents..."

    def test_tool_feedback_complete(self):
        from sunholo.adk.events import ToolFeedback, FeedbackType
        feedback = ToolFeedback.complete("search_tool", message="Found 5 results")
        assert feedback.feedback_type == FeedbackType.COMPLETE

    def test_tool_feedback_error(self):
        from sunholo.adk.events import ToolFeedback, FeedbackType
        feedback = ToolFeedback.error("search_tool", "Connection failed")
        assert feedback.feedback_type == FeedbackType.ERROR
        assert "Connection failed" in feedback.message

    def test_tool_feedback_to_marker(self):
        from sunholo.adk.events import ToolFeedback
        feedback = ToolFeedback.start("search_tool")
        marker = feedback.to_marker()
        assert "<!--TOOL_FEEDBACK:" in marker
        assert "search_tool" in marker
        assert "-->".rstrip() in marker

    def test_register_and_get_tool_display(self):
        from sunholo.adk.events import register_tool_display, get_tool_display
        register_tool_display("custom_tool", display_name="Custom Tool", icon="wrench")
        display = get_tool_display("custom_tool")
        assert display["display"] == "Custom Tool"
        assert display["icon"] == "wrench"


class TestSessionHelper:
    def test_session_keys(self):
        from sunholo.adk.session import SessionKeys
        assert SessionKeys.AUTH_TOKEN == "user:auth_token"
        assert SessionKeys.USER_ID == "user:user_id"
        assert SessionKeys.ENABLED_TOOLS == "config:enabled_tools"

    def test_mask_token(self):
        from sunholo.adk.session import _mask_token
        result = _mask_token("abcdefghijklmnop")
        assert result.startswith("***")
        assert len(result) > 3
        # Same input should produce same hash
        assert _mask_token("abcdefghijklmnop") == result
        # Empty token
        assert _mask_token("") == "<empty>"


class TestMessaging:
    def test_message_model(self):
        from sunholo.messaging.models import Message, MessageStatus, MessageType
        msg = Message(
            id="msg-1",
            title="Test",
            body="Hello",
            status=MessageStatus.UNREAD,
            message_type=MessageType.GENERAL,
        )
        assert msg.id == "msg-1"
        assert msg.status == MessageStatus.UNREAD

    def test_message_from_dict_go_style(self):
        from sunholo.messaging.models import Message
        data = {
            "ID": "msg-123",
            "Title": "Bug Report",
            "Body": "Found a bug",
            "From": "agent-1",
            "To": "inbox-main",
            "Type": "bug",
            "Status": "unread",
        }
        msg = Message.from_dict(data)
        assert msg.id == "msg-123"
        assert msg.title == "Bug Report"
        assert msg.from_agent == "agent-1"

    def test_message_from_dict_python_style(self):
        from sunholo.messaging.models import Message
        data = {
            "id": "msg-456",
            "title": "Feature Request",
            "body": "Add dark mode",
            "from_agent": "user-1",
            "to_inbox": "inbox-dev",
            "message_type": "feature",
            "status": "read",
        }
        msg = Message.from_dict(data)
        assert msg.id == "msg-456"
        assert msg.title == "Feature Request"


class TestTimeoutConfig:
    def test_get_ui_timeouts(self):
        from sunholo.utils.timeout_config import TimeoutConfig
        timeouts = TimeoutConfig.get_timeouts("ui")
        assert "stream_timeout" in timeouts
        assert "http_connect" in timeouts
        assert "genai_timeout" in timeouts

    def test_get_email_timeouts(self):
        from sunholo.utils.timeout_config import TimeoutConfig
        timeouts = TimeoutConfig.get_timeouts("email")
        ui_timeouts = TimeoutConfig.get_timeouts("ui")
        # Email should have longer timeouts than UI
        assert timeouts["stream_timeout"] >= ui_timeouts["stream_timeout"]
        assert timeouts["http_read"] >= ui_timeouts["http_read"]

    def test_get_retry_config(self):
        from sunholo.utils.timeout_config import TimeoutConfig
        config = TimeoutConfig.get_retry_config("ui")
        assert "stop_attempts" in config
        assert "wait_multiplier" in config

    def test_register_custom_profile(self):
        from sunholo.utils.timeout_config import TimeoutConfig
        custom = {"stream_timeout": 99, "http_connect": 99}
        TimeoutConfig.register_profile("custom_test", custom)
        result = TimeoutConfig.get_timeouts("custom_test")
        assert result["stream_timeout"] == 99


class TestHttpClient:
    def test_default_retry_statuses(self):
        from sunholo.utils.http_client import DEFAULT_RETRY_STATUSES
        assert 429 in DEFAULT_RETRY_STATUSES
        assert 500 in DEFAULT_RETRY_STATUSES
        assert 503 in DEFAULT_RETRY_STATUSES
        assert 200 not in DEFAULT_RETRY_STATUSES
