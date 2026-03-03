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
Dynamic agent runner for Google ADK.

Creates ADK agents dynamically at runtime based on configuration, bypassing
ADK's static agent caching to allow per-request configuration of:
- Model selection (any LiteLLM-supported model)
- Sub-agent filtering (only include enabled tools)
- Custom instructions with templating

Usage:
    from sunholo.adk.runner import DynamicRunner, SubAgentRegistry

    # Register sub-agent factories
    registry = SubAgentRegistry()
    registry.register("search", factory=create_search_agent, capability="Web search")

    # Create runner
    runner = DynamicRunner(
        registry=registry,
        session_service=session_service,
        default_model="gemini-2.5-flash",
    )

    # Run dynamically
    config = {"model": "gemini-2.5-pro", "enabled_tools": ["search"]}
    async for event in runner.run(user_id, session_id, message, config):
        yield event
"""
from __future__ import annotations

import logging
from typing import (
    TYPE_CHECKING, Any, AsyncGenerator, Callable, Dict, List, Optional,
)

if TYPE_CHECKING:
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import DatabaseSessionService
    from google.adk.artifacts import BaseArtifactService
    from google.genai import types

try:
    from google.adk.agents import Agent
    from google.adk.agents.run_config import RunConfig, StreamingMode
    from google.adk.runners import Runner
    from google.genai import types
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False

logger = logging.getLogger(__name__)

# Type alias for agent factory functions
AgentFactory = Callable[[], Any]


def _check_adk():
    if not ADK_AVAILABLE:
        raise ImportError(
            "google-adk is required. Install with: pip install sunholo[adk]"
        )


class SubAgentEntry:
    """Registration entry for a sub-agent in the registry.

    Args:
        factory: Callable that creates a fresh agent instance.
        capability: Human-readable capability description.
        delegation: Delegation instruction for the parent agent.
    """

    def __init__(
        self,
        factory: AgentFactory,
        capability: str = "",
        delegation: str = "",
    ):
        self.factory = factory
        self.capability = capability
        self.delegation = delegation


class SubAgentRegistry:
    """Registry of sub-agent factories for dynamic agent creation.

    ADK agents can only have ONE parent. When creating dynamic agents
    multiple times, we need fresh sub-agent instances each time.
    This registry stores factory functions instead of agent instances.

    Usage:
        registry = SubAgentRegistry()
        registry.register(
            "search",
            factory=lambda: Agent(model="gemini-2.5-flash", name="search", ...),
            capability="Web search and browsing",
            delegation="search_agent for web queries",
        )
    """

    def __init__(self):
        self._entries: Dict[str, SubAgentEntry] = {}
        self._always_included: List[AgentFactory] = []
        self._default_tools: List[str] = []
        self._optional_tools: List[str] = []

    def register(
        self,
        tool_id: str,
        factory: AgentFactory,
        capability: str = "",
        delegation: str = "",
        default: bool = False,
    ) -> None:
        """Register a sub-agent factory.

        Args:
            tool_id: Unique identifier for this tool/sub-agent.
            factory: Callable that creates a fresh agent instance.
            capability: Description of what this agent can do.
            delegation: Instruction for when to delegate to this agent.
            default: If True, always include (not requiring UI selection).
        """
        self._entries[tool_id] = SubAgentEntry(
            factory=factory,
            capability=capability,
            delegation=delegation,
        )
        if default:
            if tool_id not in self._default_tools:
                self._default_tools.append(tool_id)
        else:
            if tool_id not in self._optional_tools:
                self._optional_tools.append(tool_id)

    def register_always_included(self, factory: AgentFactory) -> None:
        """Register a factory for agents always included regardless of config."""
        self._always_included.append(factory)

    def get_filtered_agents(self, enabled_tools: List[str]) -> List:
        """Get fresh sub-agent instances filtered by enabled tools.

        Creates FRESH instances using factory functions to avoid
        parent reuse issues (ADK agents can only have one parent).

        Args:
            enabled_tools: List of tool IDs that are enabled.

        Returns:
            List of unique sub-agent instances.
        """
        used_factories: Dict[int, Any] = {}

        for tool_id in enabled_tools:
            if tool_id in self._entries:
                factory = self._entries[tool_id].factory
                factory_id = id(factory)
                if factory_id not in used_factories:
                    agent = factory()
                    used_factories[factory_id] = agent

        for factory in self._always_included:
            factory_id = id(factory)
            if factory_id not in used_factories:
                agent = factory()
                used_factories[factory_id] = agent

        return list(used_factories.values())

    def build_capabilities_text(self, enabled_tools: List[str]) -> str:
        """Build capabilities description from enabled tools."""
        lines = ["Your capabilities:"]
        for i, tool_id in enumerate(enabled_tools, 1):
            if tool_id in self._entries:
                cap = self._entries[tool_id].capability
                if cap:
                    lines.append(f"{i}. {cap}")
        return "\n".join(lines)

    def build_delegations_text(self, enabled_tools: List[str]) -> str:
        """Build delegation instructions from enabled tools."""
        lines = ["When to delegate to specialized agents:"]
        seen = set()
        for tool_id in enabled_tools:
            if tool_id in self._entries:
                deleg = self._entries[tool_id].delegation
                if deleg and deleg not in seen:
                    lines.append(f"- {deleg}")
                    seen.add(deleg)
        return "\n".join(lines)

    def get_disabled_descriptions(self, enabled_tools: List[str]) -> List[str]:
        """Get descriptions of disabled optional tools."""
        disabled = []
        for tool_id in self._optional_tools:
            if tool_id not in enabled_tools and tool_id in self._entries:
                cap = self._entries[tool_id].capability
                disabled.append(f"- {cap or tool_id}")
        return disabled

    @property
    def default_tools(self) -> List[str]:
        return list(self._default_tools)

    @property
    def optional_tools(self) -> List[str]:
        return list(self._optional_tools)


class ModelRegistry:
    """Registry for mapping model names to configured LLM instances.

    Supports direct model names (for Gemini/native ADK models) and
    LiteLLM-wrapped models (for Azure, OpenAI, Anthropic via LiteLLM).

    Usage:
        models = ModelRegistry(default_model="gemini-2.5-flash")
        models.register("gpt-4o", factory=lambda: AzureFixedLiteLlm(model="azure/gpt-4o"))
        model = models.get("gpt-4o")
    """

    def __init__(self, default_model: str = "gemini-2.5-flash"):
        self._factories: Dict[str, Callable] = {}
        self._cache: Dict[str, Any] = {}
        self._passthrough_prefixes: List[str] = ["gemini"]
        self.default_model = default_model

    def register(self, name: str, factory: Callable) -> None:
        """Register a model factory.

        Args:
            name: Model name as referenced in config.
            factory: Callable that creates a model instance.
        """
        self._factories[name] = factory

    def add_passthrough_prefix(self, prefix: str) -> None:
        """Add a prefix for models that should be passed through as strings."""
        if prefix not in self._passthrough_prefixes:
            self._passthrough_prefixes.append(prefix)

    def get(self, model_name: str) -> Any:
        """Get or create a model instance.

        Args:
            model_name: Model name from config.

        Returns:
            Model instance (LiteLLM wrapper) or string (for native models).
        """
        # Check passthrough prefixes (e.g. gemini models)
        for prefix in self._passthrough_prefixes:
            if model_name.startswith(prefix):
                logger.info("Using native model: %s", model_name)
                return model_name

        # Check registered factories
        if model_name in self._factories:
            if model_name not in self._cache:
                self._cache[model_name] = self._factories[model_name]()
                logger.info("Created model instance for: %s", model_name)
            return self._cache[model_name]

        # Fallback to default
        logger.warning("Unknown model '%s', falling back to %s", model_name, self.default_model)
        return self.get(self.default_model) if self.default_model != model_name else model_name


def build_instruction(
    registry: SubAgentRegistry,
    enabled_tools: List[str],
    base_instruction: str = "",
    custom_instruction: str = "",
    context_vars: Dict[str, str] | None = None,
) -> str:
    """Build agent instruction from template and enabled tools.

    Args:
        registry: Sub-agent registry for capability/delegation text.
        enabled_tools: List of enabled tool IDs.
        base_instruction: Base instruction template with {placeholders}.
            Supported placeholders: {capabilities}, {delegations},
            {available_tools}, {custom_instruction}, plus any in context_vars.
        custom_instruction: Custom instruction text from user/config.
        context_vars: Additional template variables to substitute.

    Returns:
        Formatted instruction string.
    """
    capabilities = registry.build_capabilities_text(enabled_tools)
    delegations = registry.build_delegations_text(enabled_tools)

    disabled = registry.get_disabled_descriptions(enabled_tools)
    available_tools = ""
    if disabled:
        available_tools = (
            "\nAdditional tools available (not currently enabled):\n"
            + "\n".join(disabled)
            + "\nIf the user asks for something requiring these, suggest they enable them in settings."
        )

    custom_section = ""
    if custom_instruction:
        custom_section = f"\n## Custom Instructions:\n{custom_instruction}"

    template_vars = {
        "capabilities": capabilities,
        "delegations": delegations,
        "available_tools": available_tools,
        "custom_instruction": custom_section,
    }
    if context_vars:
        template_vars.update(context_vars)

    if not base_instruction:
        base_instruction = (
            "You are an AI assistant.\n"
            "{capabilities}\n"
            "{available_tools}\n\n"
            "When a user asks for something that matches a sub-agent's capability, "
            "delegate to that agent.\n\n"
            "{delegations}\n"
            "{custom_instruction}"
        )

    try:
        return base_instruction.format(**template_vars)
    except KeyError as e:
        logger.warning("Missing template variable in instruction: %s", e)
        return base_instruction


def dict_to_content(message_dict: Dict[str, Any]):
    """Convert a message dict to an ADK Content object.

    Args:
        message_dict: Dict with 'role' and 'parts' keys.
            e.g. {"role": "user", "parts": [{"text": "hello"}]}

    Returns:
        types.Content object suitable for ADK Runner.
    """
    _check_adk()
    role = message_dict.get("role", "user")
    parts_data = message_dict.get("parts", [])

    parts = []
    for part in parts_data:
        if isinstance(part, dict) and "text" in part:
            parts.append(types.Part(text=part["text"]))
        elif isinstance(part, str):
            parts.append(types.Part(text=part))

    return types.Content(role=role, parts=parts)


class DynamicRunner:
    """Creates and runs ADK agents dynamically based on per-request config.

    This bypasses ADK's static agent caching to allow per-request
    configuration of model, tools, and instructions.

    Args:
        registry: Sub-agent registry with tool factories.
        session_service: ADK session service.
        artifact_service: ADK artifact service (optional).
        model_registry: Model registry for name-to-instance mapping.
        app_name: Application name for the ADK Runner.
        base_instruction: Base instruction template.
        agent_name: Name for the dynamic parent agent.
        default_tools: List of additional tools always available.
    """

    def __init__(
        self,
        registry: SubAgentRegistry,
        session_service: Any,
        artifact_service: Any = None,
        model_registry: ModelRegistry | None = None,
        app_name: str = "dynamic",
        base_instruction: str = "",
        agent_name: str = "dynamic_assistant",
        default_tools: List | None = None,
    ):
        _check_adk()
        self.registry = registry
        self.session_service = session_service
        self.artifact_service = artifact_service
        self.model_registry = model_registry or ModelRegistry()
        self.app_name = app_name
        self.base_instruction = base_instruction
        self.agent_name = agent_name
        self.default_tools = default_tools or []

    def create_agent(self, config: Dict[str, Any]) -> Agent:
        """Create an ADK Agent dynamically based on configuration.

        Args:
            config: Dictionary with:
                - model: Model name (e.g. "gemini-2.5-flash")
                - enabled_tools: List of tool IDs to enable
                - instruction: Custom instruction text
                - Any additional keys for context_vars in the template

        Returns:
            Configured Agent instance.
        """
        model_name = config.get("model", self.model_registry.default_model)
        ui_selected_tools = config.get("enabled_tools", [])
        custom_instruction = config.get("instruction", "")

        # Combine default tools with UI-selected optional tools
        enabled_tools = list(self.registry.default_tools)
        for tool in ui_selected_tools:
            if tool in self.registry.optional_tools and tool not in enabled_tools:
                enabled_tools.append(tool)

        # Get model
        model = self.model_registry.get(model_name)

        # Get filtered sub-agents
        sub_agents = self.registry.get_filtered_agents(enabled_tools)

        # Build context variables from config (exclude known keys)
        known_keys = {"model", "enabled_tools", "instruction"}
        context_vars = {k: str(v) for k, v in config.items() if k not in known_keys and isinstance(v, str)}

        # Build instruction
        instruction = build_instruction(
            registry=self.registry,
            enabled_tools=enabled_tools,
            base_instruction=self.base_instruction,
            custom_instruction=custom_instruction,
            context_vars=context_vars,
        )

        agent = Agent(
            model=model,
            name=self.agent_name,
            instruction=instruction,
            sub_agents=sub_agents,
            tools=list(self.default_tools),
        )

        logger.info(
            "Dynamic agent created: %d sub-agents (%s), model=%s",
            len(sub_agents),
            [a.name for a in sub_agents],
            model_name,
        )
        return agent

    async def run(
        self,
        user_id: str,
        session_id: str,
        new_message: Dict[str, Any],
        config: Dict[str, Any],
        streaming_mode: str = "SSE",
    ) -> AsyncGenerator:
        """Create and run a dynamic agent, yielding events.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            new_message: Message dict with 'role' and 'parts'.
            config: Agent configuration dict.
            streaming_mode: Streaming mode ("SSE" or "NONE").

        Yields:
            ADK events from the agent run.
        """
        agent = self.create_agent(config)

        runner = Runner(
            app_name=self.app_name,
            agent=agent,
            session_service=self.session_service,
            artifact_service=self.artifact_service,
        )

        content = dict_to_content(new_message)

        mode = StreamingMode.SSE if streaming_mode == "SSE" else StreamingMode.NONE
        run_config = RunConfig(streaming_mode=mode)

        logger.info("Running dynamic agent for user=%s, session=%s", user_id, session_id)

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
            run_config=run_config,
        ):
            yield event
