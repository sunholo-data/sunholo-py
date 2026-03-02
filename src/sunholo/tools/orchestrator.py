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
Tool orchestration for coordinating async tool execution.

Provides a framework for running multiple tools concurrently with:
- Task mapping (tool name -> handler function + args)
- Async execution via AsyncTaskRunner
- Result aggregation and streaming
- Config merging (user configs + defaults)
- Context-aware timeouts

Usage:
    from sunholo.tools.orchestrator import ToolOrchestrator

    orchestrator = ToolOrchestrator()
    orchestrator.register("search", search_handler, capability="Search the web")
    orchestrator.register("email", email_handler, capability="Search emails")

    results = await orchestrator.run(
        tools=["search", "email"],
        question="Find recent reports",
        tool_configs={"search": {"max_results": 10}},
    )
"""
from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Type alias for tool handler functions
ToolHandler = Callable[..., Any]


class ToolEntry:
    """Registration entry for a tool in the orchestrator.

    Args:
        handler: Async callable that executes the tool.
        capability: Human-readable capability description.
        default_args: Default arguments passed to the handler.
    """

    def __init__(
        self,
        handler: ToolHandler,
        capability: str = "",
        default_args: Dict[str, Any] | None = None,
    ):
        self.handler = handler
        self.capability = capability
        self.default_args = default_args or {}


class ToolOrchestrator:
    """Coordinates async execution of multiple tools.

    Manages a registry of tool handlers and executes them concurrently
    using AsyncTaskRunner, aggregating results as they complete.

    Args:
        context: Execution context for timeout configuration ("ui", "email", etc.).
        max_concurrent: Maximum concurrent tool executions.
    """

    def __init__(self, context: str = "ui", max_concurrent: int = 10):
        self.context = context
        self.max_concurrent = max_concurrent
        self._tools: Dict[str, ToolEntry] = {}

    def register(
        self,
        tool_id: str,
        handler: ToolHandler,
        capability: str = "",
        default_args: Dict[str, Any] | None = None,
    ) -> None:
        """Register a tool handler.

        Args:
            tool_id: Unique tool identifier.
            handler: Async callable that executes the tool.
            capability: Human-readable capability description.
            default_args: Default arguments for the handler.
        """
        self._tools[tool_id] = ToolEntry(
            handler=handler,
            capability=capability,
            default_args=default_args,
        )

    def list_tools(self) -> List[Dict[str, str]]:
        """List all registered tools.

        Returns:
            List of dicts with "id" and "capability" keys.
        """
        return [
            {"id": tid, "capability": entry.capability}
            for tid, entry in self._tools.items()
        ]

    def merge_tool_configs(
        self,
        tools: List[str],
        user_configs: Dict[str, Any] | None = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Merge user configs with default tool configs.

        For each requested tool, merges:
        1. Registered default_args
        2. User-provided configs (overrides defaults)

        Args:
            tools: List of tool IDs to configure.
            user_configs: User-provided per-tool configs.

        Returns:
            Dict mapping tool_id -> merged config dict.
        """
        result: Dict[str, Dict[str, Any]] = {}
        user_configs = user_configs or {}

        for tool_id in tools:
            if tool_id not in self._tools:
                continue

            # Start with registered defaults
            merged = dict(self._tools[tool_id].default_args)

            # Override with user configs
            if tool_id in user_configs:
                user_cfg = user_configs[tool_id]
                if isinstance(user_cfg, dict):
                    for key, value in user_cfg.items():
                        if value is not None and value != "":
                            merged[key] = value

            result[tool_id] = merged

        return result

    async def run(
        self,
        tools: List[str],
        question: str = "",
        tool_configs: Dict[str, Any] | None = None,
        common_args: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Execute multiple tools concurrently and aggregate results.

        Args:
            tools: List of tool IDs to execute.
            question: The user question/query to pass to tools.
            tool_configs: Per-tool configuration overrides.
            common_args: Args passed to all tool handlers.

        Returns:
            Dict with:
                - "results": Dict mapping tool_id -> result
                - "errors": Dict mapping tool_id -> error message
                - "completed": List of successfully completed tool IDs
        """
        from sunholo.invoke import AsyncTaskRunner

        merged = self.merge_tool_configs(tools, tool_configs)
        common = common_args or {}

        runner = AsyncTaskRunner(context=self.context)

        # Add tasks
        for tool_id in tools:
            if tool_id not in self._tools:
                logger.warning("Unknown tool: %s (skipping)", tool_id)
                continue

            entry = self._tools[tool_id]
            tool_args = dict(merged.get(tool_id, {}))
            tool_args.update(common)
            if question:
                tool_args["question"] = question

            runner.add_task(
                name=tool_id,
                func=entry.handler,
                **tool_args,
            )

        # Execute and collect results
        results: Dict[str, Any] = {}
        errors: Dict[str, str] = {}
        completed: List[str] = []

        async for task_result in runner.run_async_as_completed():
            msg_type = task_result.get("type", "")
            name = task_result.get("name", "")

            if msg_type == "task_complete":
                results[name] = task_result.get("result")
                completed.append(name)
                logger.info("Tool completed: %s", name)
            elif msg_type == "task_error":
                errors[name] = str(task_result.get("error", "Unknown error"))
                logger.error("Tool failed: %s - %s", name, errors[name])
            elif msg_type == "heartbeat":
                logger.debug("Tool heartbeat: %s", name)

        return {
            "results": results,
            "errors": errors,
            "completed": completed,
        }

    async def run_streaming(
        self,
        tools: List[str],
        question: str = "",
        tool_configs: Dict[str, Any] | None = None,
        common_args: Dict[str, Any] | None = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute tools and yield results as they complete.

        Same as run() but yields individual results as an async generator.

        Yields:
            Dicts with "type" ("result" or "error"), "tool_id", and payload.
        """
        from sunholo.invoke import AsyncTaskRunner

        merged = self.merge_tool_configs(tools, tool_configs)
        common = common_args or {}

        runner = AsyncTaskRunner(context=self.context)

        for tool_id in tools:
            if tool_id not in self._tools:
                continue
            entry = self._tools[tool_id]
            tool_args = dict(merged.get(tool_id, {}))
            tool_args.update(common)
            if question:
                tool_args["question"] = question
            runner.add_task(name=tool_id, func=entry.handler, **tool_args)

        async for task_result in runner.run_async_as_completed():
            msg_type = task_result.get("type", "")
            name = task_result.get("name", "")

            if msg_type == "task_complete":
                yield {"type": "result", "tool_id": name, "result": task_result.get("result")}
            elif msg_type == "task_error":
                yield {"type": "error", "tool_id": name, "error": str(task_result.get("error", ""))}
