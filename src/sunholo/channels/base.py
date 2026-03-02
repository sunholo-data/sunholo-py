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
Abstract base class for messaging channel integrations.

All channel implementations (email, Telegram, WhatsApp) should inherit
from BaseChannel and implement the required methods.

Usage:
    from sunholo.channels.base import BaseChannel, ChannelMessage, ChannelResponse

    class MyChannel(BaseChannel):
        async def receive_webhook(self, request):
            ...
        async def send_response(self, channel_id, response):
            ...
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Supported channel types."""
    EMAIL = "email"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    WEBHOOK = "webhook"


@dataclass
class ChannelMessage:
    """Normalized incoming message from any channel.

    This is the standard format that channels convert incoming
    platform-specific messages into for processing.
    """
    channel_type: ChannelType
    channel_id: str  # Platform-specific sender ID (email, chat_id, phone)
    user_id: str  # Normalized user identifier
    text: str  # Message text content
    subject: str = ""  # Subject line (email) or empty
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    reply_to: str = ""  # ID of message being replied to
    thread_id: str = ""  # Conversation thread ID


@dataclass
class ChannelResponse:
    """Response to send back through a channel.

    The channel implementation handles converting this to the
    platform-specific format (HTML email, Telegram markdown, etc.).
    """
    text: str  # Main response text
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    format: str = "markdown"  # "markdown", "html", "plain"


class BaseChannel(ABC):
    """Abstract base class for messaging channel integrations.

    Subclasses must implement:
    - receive_webhook(): Parse incoming platform webhook
    - send_response(): Send a response back to the platform
    - validate_webhook(): Validate webhook authenticity

    Optional overrides:
    - format_message(): Platform-specific message formatting
    - get_session_id(): Extract/generate session ID for the conversation
    """

    def __init__(self, channel_type: ChannelType, config: Dict[str, Any] | None = None):
        self.channel_type = channel_type
        self.config = config or {}
        self._rate_limits: Dict[str, List[float]] = {}

    @abstractmethod
    async def receive_webhook(self, request: Any) -> Optional[ChannelMessage]:
        """Parse an incoming webhook request into a ChannelMessage.

        Args:
            request: The incoming HTTP request (FastAPI Request).

        Returns:
            Parsed ChannelMessage, or None if the webhook should be ignored
            (e.g., status callbacks, duplicate messages).
        """
        ...

    @abstractmethod
    async def send_response(
        self, channel_id: str, response: ChannelResponse
    ) -> bool:
        """Send a response back through the channel.

        Args:
            channel_id: Platform-specific destination (email, chat_id, phone).
            response: The response to send.

        Returns:
            True if sent successfully.
        """
        ...

    @abstractmethod
    async def validate_webhook(self, request: Any) -> bool:
        """Validate that a webhook request is authentic.

        Args:
            request: The incoming HTTP request.

        Returns:
            True if the webhook is valid (correct signature, etc.).
        """
        ...

    def format_message(self, text: str, format_type: str = "markdown") -> str:
        """Convert text to the channel's native format.

        Override in subclasses for platform-specific formatting
        (e.g., Telegram MarkdownV2, WhatsApp formatting, HTML email).

        Args:
            text: Input text (typically markdown).
            format_type: Input format ("markdown", "html", "plain").

        Returns:
            Formatted text for the platform.
        """
        return text

    def get_session_id(self, message: ChannelMessage) -> str:
        """Generate a session ID for the conversation.

        Override for platform-specific session logic.

        Args:
            message: The incoming message.

        Returns:
            Session identifier string.
        """
        return f"{self.channel_type.value}:{message.channel_id}"

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 10,
        window_seconds: float = 60.0,
    ) -> bool:
        """Check if a sender is within rate limits.

        Args:
            identifier: The sender identifier to rate limit.
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.

        Returns:
            True if the request is allowed, False if rate limited.
        """
        now = time.time()
        if identifier not in self._rate_limits:
            self._rate_limits[identifier] = []

        # Clean old entries
        self._rate_limits[identifier] = [
            t for t in self._rate_limits[identifier]
            if now - t < window_seconds
        ]

        if len(self._rate_limits[identifier]) >= max_requests:
            logger.warning(
                "Rate limit exceeded for %s on %s channel",
                identifier, self.channel_type.value
            )
            return False

        self._rate_limits[identifier].append(now)
        return True
