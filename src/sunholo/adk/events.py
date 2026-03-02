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
ADK event transformer for SSE streaming.

Transforms raw ADK events into UI-ready events with standardized
ToolFeedback markers. Handles function call/response pairing and
stream lifecycle markers.

Usage:
    from sunholo.adk.events import EventTransformer

    transformer = EventTransformer()
    async for event in runner.run_async(...):
        ui_events = transformer.transform(event)
        for ui_event in ui_events:
            yield ui_event
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of tool feedback events."""
    START = "start"
    COMPLETE = "complete"
    ERROR = "error"
    STREAM_START = "stream_start"
    STREAM_END = "stream_end"


@dataclass
class ToolFeedback:
    """Standardized UI feedback for tool execution lifecycle.

    Embedded as HTML comments in streaming responses so they can be
    parsed by frontends without affecting rendered content.

    Format: <!--TOOL_FEEDBACK:{json}-->
    """
    tool_name: str
    feedback_type: FeedbackType
    display_name: str = ""
    message: str = ""
    icon: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_marker(self) -> str:
        """Serialize to HTML comment marker for embedding in SSE streams."""
        payload = {
            "tool": self.tool_name,
            "type": self.feedback_type.value,
            "display": self.display_name or self.tool_name,
            "message": self.message,
        }
        if self.icon:
            payload["icon"] = self.icon
        if self.metadata:
            payload["metadata"] = self.metadata
        return f"<!--TOOL_FEEDBACK:{json.dumps(payload)}-->"

    @classmethod
    def start(cls, tool_name: str, display_name: str = "", message: str = "", **kwargs) -> "ToolFeedback":
        """Create a tool start feedback event."""
        return cls(
            tool_name=tool_name,
            feedback_type=FeedbackType.START,
            display_name=display_name or tool_name,
            message=message or f"Using {display_name or tool_name}...",
            **kwargs,
        )

    @classmethod
    def complete(cls, tool_name: str, display_name: str = "", message: str = "", **kwargs) -> "ToolFeedback":
        """Create a tool complete feedback event."""
        return cls(
            tool_name=tool_name,
            feedback_type=FeedbackType.COMPLETE,
            display_name=display_name or tool_name,
            message=message or f"Finished {display_name or tool_name}",
            **kwargs,
        )

    @classmethod
    def error(cls, tool_name: str, error_msg: str = "", **kwargs) -> "ToolFeedback":
        """Create a tool error feedback event."""
        return cls(
            tool_name=tool_name,
            feedback_type=FeedbackType.ERROR,
            message=error_msg or f"Error in {tool_name}",
            **kwargs,
        )


# Default tool display configuration - can be extended via register_tool_display()
_TOOL_DISPLAY_CONFIG: Dict[str, Dict[str, str]] = {
    "load_artifacts": {"display": "Loading Files", "icon": "📎"},
    "transfer_to_agent": {"display": "Delegating to Agent", "icon": "🔄"},
    "google_search": {"display": "Searching the Web", "icon": "🔍"},
}


def register_tool_display(tool_name: str, display_name: str, icon: str = "") -> None:
    """Register a custom tool display configuration.

    Args:
        tool_name: Internal tool name (as used in ADK).
        display_name: User-friendly display name.
        icon: Optional emoji icon.
    """
    _TOOL_DISPLAY_CONFIG[tool_name] = {"display": display_name, "icon": icon}


def get_tool_display(tool_name: str) -> Dict[str, str]:
    """Get display info for a tool, with fallback to the tool name itself."""
    return _TOOL_DISPLAY_CONFIG.get(tool_name, {"display": tool_name, "icon": "🔧"})


class EventTransformer:
    """Transforms raw ADK events into UI-ready events with ToolFeedback markers.

    Tracks active tool calls to pair function_call events with their
    corresponding function_response events.

    Args:
        start_message: Message to include in stream start marker.
    """

    def __init__(self, start_message: str = "Processing your request..."):
        self._active_tools: Dict[str, str] = {}  # call_id -> tool_name
        self._started = False
        self._start_message = start_message

    def transform(self, event: Any) -> List[str]:
        """Transform an ADK event into a list of UI-ready string chunks.

        Args:
            event: An ADK Event object (from google.adk.events).

        Returns:
            List of string chunks to yield in the SSE stream.
            May include ToolFeedback markers embedded as HTML comments.
        """
        chunks: List[str] = []

        # Stream start marker
        if not self._started:
            self._started = True
            start_fb = ToolFeedback(
                tool_name="stream",
                feedback_type=FeedbackType.STREAM_START,
                message=self._start_message,
            )
            chunks.append(start_fb.to_marker())

        # Extract content from event (ADK event structure)
        content = getattr(event, "content", None)
        if content is None:
            return chunks

        parts = getattr(content, "parts", None) or []
        for part in parts:
            # Text content
            text = getattr(part, "text", None)
            if text:
                chunks.append(text)

            # Function call (tool start)
            fn_call = getattr(part, "function_call", None)
            if fn_call:
                call_name = getattr(fn_call, "name", "unknown")
                call_id = getattr(fn_call, "id", call_name)
                self._active_tools[call_id] = call_name
                display = get_tool_display(call_name)
                fb = ToolFeedback.start(
                    tool_name=call_name,
                    display_name=display["display"],
                    icon=display.get("icon", ""),
                )
                chunks.append(fb.to_marker())

            # Function response (tool complete)
            fn_resp = getattr(part, "function_response", None)
            if fn_resp:
                resp_name = getattr(fn_resp, "name", "unknown")
                resp_id = getattr(fn_resp, "id", resp_name)
                # Try to match with active tool
                matched_name = self._active_tools.pop(resp_id, resp_name)
                display = get_tool_display(matched_name)
                fb = ToolFeedback.complete(
                    tool_name=matched_name,
                    display_name=display["display"],
                    icon=display.get("icon", ""),
                )
                chunks.append(fb.to_marker())

        return chunks

    def stream_end(self) -> str:
        """Generate stream end marker."""
        fb = ToolFeedback(
            tool_name="stream",
            feedback_type=FeedbackType.STREAM_END,
            message="Response complete",
        )
        return fb.to_marker()
