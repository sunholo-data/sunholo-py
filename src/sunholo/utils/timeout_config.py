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
Context-aware timeout configuration for different operational contexts.

Provides optimized timeout profiles for:
- UI requests: Fast timeouts for responsive user experience
- Email/API/background: Extended timeouts for complex processing
- MCP/browser automation: Very long timeouts for extended operations

Usage:
    from sunholo.utils.timeout_config import TimeoutConfig

    # Get all timeouts for a context
    timeouts = TimeoutConfig.get_timeouts("email")

    # Get specific timeout value
    stream_timeout = TimeoutConfig.get_timeout("stream_timeout", context="ui")

    # Get HTTP client timeouts
    http_timeouts = TimeoutConfig.get_http_timeouts("mcp")

    # Get retry config for tenacity
    retry_config = TimeoutConfig.get_retry_config("email")
"""
from __future__ import annotations

import os
from typing import Any, Dict


class TimeoutConfig:
    """Centralized timeout configuration with context awareness."""

    UI_TIMEOUTS: Dict[str, Any] = {
        "stream_timeout": 120,
        "tool_heartbeat": 120,
        "tool_hard_timeout": 600,
        "http_connect": 30.0,
        "http_read": 30.0,
        "http_write": 60.0,
        "http_pool": 90.0,
        "genai_timeout": 60000,
        "retry_attempts": 7,
        "retry_multiplier": 1,
        "retry_min": 1,
        "retry_max": 32,
        "quarto_export": 120,
        "file_download": 60,
        "attachment_download": 30,
        "mailgun_api": 30,
    }

    MCP_TIMEOUTS: Dict[str, Any] = {
        "stream_timeout": 1800,
        "tool_heartbeat": 600,
        "tool_hard_timeout": 3600,
        "http_connect": 120.0,
        "http_read": 600.0,
        "http_write": 300.0,
        "http_pool": 600.0,
        "genai_timeout": 600000,
        "retry_attempts": 3,
        "retry_multiplier": 2,
        "retry_min": 10,
        "retry_max": 300,
        "quarto_export": 600,
        "file_download": 300,
        "attachment_download": 180,
        "mailgun_api": 120,
    }

    EMAIL_API_TIMEOUTS: Dict[str, Any] = {
        "stream_timeout": 1800,
        "tool_heartbeat": 300,
        "tool_hard_timeout": 3000,
        "http_connect": 60.0,
        "http_read": 300.0,
        "http_write": 300.0,
        "http_pool": 300.0,
        "genai_timeout": 300000,
        "retry_attempts": 5,
        "retry_multiplier": 2,
        "retry_min": 5,
        "retry_max": 300,
        "quarto_export": 600,
        "file_download": 300,
        "attachment_download": 180,
        "mailgun_api": 120,
    }

    # Custom profiles registry for extensibility
    _custom_profiles: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_profile(cls, name: str, timeouts: Dict[str, Any]) -> None:
        """Register a custom timeout profile.

        Args:
            name: Profile name (e.g., "batch", "realtime").
            timeouts: Timeout configuration dictionary.
        """
        cls._custom_profiles[name] = timeouts.copy()

    @classmethod
    def get_timeouts(cls, context: str = "ui") -> Dict[str, Any]:
        """Get timeout configuration based on context.

        Args:
            context: Context type - "ui", "mcp", "email", "api",
                "background", "whatsapp", "telegram", or a custom profile name.

        Returns:
            Timeout configuration dictionary.
        """
        if context in cls._custom_profiles:
            return cls._custom_profiles[context].copy()
        if context == "mcp":
            return cls.MCP_TIMEOUTS.copy()
        if context in ("email", "api", "background", "whatsapp", "telegram"):
            return cls.EMAIL_API_TIMEOUTS.copy()
        return cls.UI_TIMEOUTS.copy()

    @classmethod
    def get_timeout(cls, key: str, context: str = "ui", default: Any = 30) -> Any:
        """Get a specific timeout value with context awareness.

        Args:
            key: Timeout key to retrieve.
            context: Context type.
            default: Default value if key not found.

        Returns:
            Timeout value.
        """
        timeouts = cls.get_timeouts(context)
        return timeouts.get(key, default)

    @classmethod
    def get_retry_config(cls, context: str = "ui") -> Dict[str, Any]:
        """Get tenacity retry configuration for the given context.

        Args:
            context: Context type.

        Returns:
            Dict with keys: stop_attempts, wait_multiplier, wait_min, wait_max.
        """
        timeouts = cls.get_timeouts(context)
        return {
            "stop_attempts": timeouts.get("retry_attempts", 3),
            "wait_multiplier": timeouts.get("retry_multiplier", 1),
            "wait_min": timeouts.get("retry_min", 1),
            "wait_max": timeouts.get("retry_max", 32),
        }

    @classmethod
    def get_http_timeouts(cls, context: str = "ui") -> Dict[str, float]:
        """Get HTTP client timeout configuration for the given context.

        Args:
            context: Context type.

        Returns:
            Dict with keys: connect, read, write, pool.
        """
        timeouts = cls.get_timeouts(context)
        return {
            "connect": timeouts.get("http_connect", 30.0),
            "read": timeouts.get("http_read", 30.0),
            "write": timeouts.get("http_write", 60.0),
            "pool": timeouts.get("http_pool", 90.0),
        }


def detect_request_context() -> str:
    """Auto-detect request context from environment.

    Returns:
        Detected context string ("ui", "email", "mcp", etc.).
    """
    if os.getenv("EMAIL_PROCESSING_MODE") == "true":
        return "email"
    if os.getenv("MCP_MODE") == "true":
        return "mcp"
    return "ui"
