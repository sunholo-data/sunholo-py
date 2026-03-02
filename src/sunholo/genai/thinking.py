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
Extended thinking content capture for LLM responses.

Extracts and processes "thinking" or "reasoning" content from model
responses that support extended thinking (e.g., Anthropic Claude with
extended thinking, Google Gemini with thinking mode).

Supports:
- Tag-based extraction (<thinking>...</thinking>, <antThinking>...</antThinking>)
- Streaming callback wrapping for real-time thinking capture
- Multi-format thinking content (text blocks, tagged sections)
- Thinking content aggregation across streaming chunks

Usage:
    from sunholo.genai.thinking import ThinkingCapture, extract_thinking

    # Extract thinking from a complete response
    thinking, response = extract_thinking(full_text)

    # Capture thinking during streaming
    capture = ThinkingCapture()
    for chunk in stream:
        capture.process_chunk(chunk)
    thinking_text = capture.get_thinking()
    response_text = capture.get_response()
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Common thinking tag patterns
THINKING_PATTERNS = [
    (re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL), "thinking"),
    (re.compile(r"<antThinking>(.*?)</antThinking>", re.DOTALL), "antThinking"),
    (re.compile(r"<reflection>(.*?)</reflection>", re.DOTALL), "reflection"),
]


@dataclass
class ThinkingContent:
    """Captured thinking content from a model response.

    Attributes:
        text: The thinking text content.
        tag_type: The type of thinking tag (e.g., "thinking", "antThinking").
        metadata: Additional metadata about the thinking content.
    """

    text: str = ""
    tag_type: str = "thinking"
    metadata: Dict[str, Any] = field(default_factory=dict)


def extract_thinking(
    text: str,
    patterns: List[Tuple[re.Pattern, str]] | None = None,
    remove_tags: bool = True,
) -> Tuple[List[ThinkingContent], str]:
    """Extract thinking content from a complete text response.

    Finds and extracts all thinking-tagged sections from the text.

    Args:
        text: Full response text that may contain thinking tags.
        patterns: Custom regex patterns to use. Each tuple is (pattern, tag_type).
            Defaults to THINKING_PATTERNS.
        remove_tags: If True, return the text with thinking tags removed.

    Returns:
        Tuple of (thinking_contents, cleaned_text).
        - thinking_contents: List of ThinkingContent objects found
        - cleaned_text: Original text with thinking sections removed (if remove_tags)
    """
    if not text:
        return [], ""

    search_patterns = patterns or THINKING_PATTERNS
    thinking_contents: List[ThinkingContent] = []
    cleaned = text

    for pattern, tag_type in search_patterns:
        matches = pattern.finditer(text)
        for match in matches:
            content = match.group(1).strip()
            if content:
                thinking_contents.append(
                    ThinkingContent(text=content, tag_type=tag_type)
                )
            if remove_tags:
                cleaned = cleaned.replace(match.group(0), "")

    # Clean up extra whitespace from removal
    if remove_tags and thinking_contents:
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    return thinking_contents, cleaned


def extract_thinking_simple(text: str) -> Tuple[str, str]:
    """Simple extraction returning just thinking text and cleaned response.

    Convenience wrapper around extract_thinking() for cases where
    you just need the text strings.

    Args:
        text: Full response text.

    Returns:
        Tuple of (thinking_text, response_text).
        thinking_text is all thinking sections joined with newlines.
    """
    contents, cleaned = extract_thinking(text)
    thinking_text = "\n\n".join(c.text for c in contents)
    return thinking_text, cleaned


class ThinkingCapture:
    """Captures thinking content from streaming responses.

    Wraps a streaming response to intercept and separate thinking
    content from the main response in real-time.

    Usage:
        capture = ThinkingCapture()
        for chunk in stream:
            capture.process_chunk(chunk)
        thinking = capture.get_thinking()
        response = capture.get_response()
    """

    def __init__(self, tag: str = "thinking"):
        """Initialize thinking capture.

        Args:
            tag: The thinking tag name to look for (default: "thinking").
        """
        self._tag = tag
        self._open_tag = f"<{tag}>"
        self._close_tag = f"</{tag}>"
        self._thinking_parts: List[str] = []
        self._response_parts: List[str] = []
        self._in_thinking = False
        self._buffer = ""

    def process_chunk(self, chunk: str) -> Optional[str]:
        """Process a streaming chunk, separating thinking from response.

        Args:
            chunk: A text chunk from the stream.

        Returns:
            The non-thinking portion of the chunk (may be empty string
            if the chunk is entirely thinking content), or None if
            still buffering.
        """
        self._buffer += chunk
        response_out = []

        while self._buffer:
            if self._in_thinking:
                # Look for closing tag
                close_pos = self._buffer.find(self._close_tag)
                if close_pos >= 0:
                    # Found closing tag
                    thinking_text = self._buffer[:close_pos]
                    self._thinking_parts.append(thinking_text)
                    self._buffer = self._buffer[close_pos + len(self._close_tag):]
                    self._in_thinking = False
                else:
                    # Still in thinking, buffer everything
                    # But check if we might have a partial closing tag
                    partial_match = False
                    for i in range(1, len(self._close_tag)):
                        if self._buffer.endswith(self._close_tag[:i]):
                            partial_match = True
                            safe = self._buffer[:-i]
                            if safe:
                                self._thinking_parts.append(safe)
                            self._buffer = self._buffer[-i:]
                            break
                    if not partial_match:
                        self._thinking_parts.append(self._buffer)
                        self._buffer = ""
                    break
            else:
                # Look for opening tag
                open_pos = self._buffer.find(self._open_tag)
                if open_pos >= 0:
                    # Found opening tag
                    before = self._buffer[:open_pos]
                    if before:
                        response_out.append(before)
                        self._response_parts.append(before)
                    self._buffer = self._buffer[open_pos + len(self._open_tag):]
                    self._in_thinking = True
                else:
                    # Check for partial opening tag at end
                    partial_match = False
                    for i in range(1, len(self._open_tag)):
                        if self._buffer.endswith(self._open_tag[:i]):
                            partial_match = True
                            safe = self._buffer[:-i]
                            if safe:
                                response_out.append(safe)
                                self._response_parts.append(safe)
                            self._buffer = self._buffer[-i:]
                            break
                    if not partial_match:
                        response_out.append(self._buffer)
                        self._response_parts.append(self._buffer)
                        self._buffer = ""
                    break

        return "".join(response_out) if response_out else ""

    def flush(self) -> str:
        """Flush any remaining buffer content.

        Call this when the stream ends to get any remaining content.

        Returns:
            Any remaining non-thinking content.
        """
        if self._buffer:
            if self._in_thinking:
                self._thinking_parts.append(self._buffer)
                self._buffer = ""
                return ""
            else:
                remaining = self._buffer
                self._response_parts.append(remaining)
                self._buffer = ""
                return remaining
        return ""

    def get_thinking(self) -> str:
        """Get all captured thinking content.

        Returns:
            Concatenated thinking text.
        """
        return "".join(self._thinking_parts)

    def get_response(self) -> str:
        """Get all captured response content (non-thinking).

        Returns:
            Concatenated response text.
        """
        return "".join(self._response_parts)

    @property
    def is_in_thinking(self) -> bool:
        """Whether we're currently inside a thinking block."""
        return self._in_thinking

    def reset(self) -> None:
        """Reset capture state for reuse."""
        self._thinking_parts.clear()
        self._response_parts.clear()
        self._in_thinking = False
        self._buffer = ""


def extract_anthropic_thinking(response: Any) -> Tuple[str, str]:
    """Extract thinking content from an Anthropic API response.

    Handles the Anthropic extended thinking format where thinking
    content appears as separate content blocks with type="thinking".

    Args:
        response: Anthropic API response object (Message).

    Returns:
        Tuple of (thinking_text, response_text).
    """
    thinking_parts = []
    response_parts = []

    content_blocks = getattr(response, "content", [])
    if not content_blocks:
        return "", ""

    for block in content_blocks:
        block_type = getattr(block, "type", "")
        if block_type == "thinking":
            thinking_parts.append(getattr(block, "thinking", ""))
        elif block_type == "text":
            response_parts.append(getattr(block, "text", ""))

    return "\n".join(thinking_parts), "\n".join(response_parts)


def create_thinking_callback(
    on_thinking: Callable[[str], None],
    on_response: Callable[[str], None],
    tag: str = "thinking",
) -> Callable[[str], None]:
    """Create a streaming callback that separates thinking from response.

    Factory function that creates a callback suitable for use with
    streaming LLM responses. The callback routes thinking content
    and response content to separate handlers.

    Args:
        on_thinking: Called with thinking content chunks.
        on_response: Called with response content chunks.
        tag: Thinking tag name to detect.

    Returns:
        A callback function that accepts text chunks.
    """
    capture = ThinkingCapture(tag=tag)

    def callback(chunk: str) -> None:
        response_text = capture.process_chunk(chunk)
        if response_text:
            on_response(response_text)
        # Check if new thinking content was added
        thinking = capture.get_thinking()
        if thinking and capture.is_in_thinking:
            on_thinking(chunk)

    return callback
