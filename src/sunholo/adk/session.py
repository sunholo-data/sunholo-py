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
ADK session management with auth and config injection.

Provides helpers for creating and updating ADK sessions with
embedded authentication tokens and agent configuration.

Usage:
    from sunholo.adk.session import SessionHelper

    helper = SessionHelper(session_service)
    session = await helper.create_session(
        app_name="my_agent",
        user_id="user123",
        auth_token="jwt_token",
        config={"enabled_tools": ["search", "browse"]},
    )
"""
from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from google.adk.sessions import DatabaseSessionService

logger = logging.getLogger(__name__)


# Standard session state key prefixes
class SessionKeys:
    """Standard session state keys for auth and configuration.

    These keys follow a namespace convention:
    - user:* - User identity and authentication
    - config:* - Agent configuration
    """
    # Auth keys
    AUTH_TOKEN = "user:auth_token"
    USER_ID = "user:user_id"
    USERNAME = "user:username"
    GRAPH_TOKEN = "user:graph_token"
    THREAD_ID = "user:thread_id"
    TIMEZONE = "user:timezone"
    ASSISTANT_ID = "user:assistant_id"

    # Config keys
    ENABLED_TOOLS = "config:enabled_tools"
    MODEL = "config:model"
    INSTRUCTION = "config:instruction"
    DEEP_TOGGLE = "config:deep_toggle"
    COUNTRY = "config:country"
    CITY = "config:city"

    # Agent tracking
    ACTIVE_ASSISTANT = "active_assistant"
    ROOT_ASSISTANT_ID = "root_assistant_id"


def _mask_token(token: str, visible_chars: int = 8) -> str:
    """Mask a token for safe logging, showing hash prefix."""
    if not token:
        return "<empty>"
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:visible_chars]
    return f"***{token_hash}"


class SessionHelper:
    """Manages ADK session creation and state updates.

    Encapsulates session state key management and provides
    a clean interface for injecting auth tokens, user config,
    and agent settings into sessions.

    Args:
        session_service: An ADK DatabaseSessionService instance.
    """

    def __init__(self, session_service: DatabaseSessionService):
        self._session_service = session_service

    async def create_session(
        self,
        app_name: str,
        user_id: str,
        *,
        auth_token: str = "",
        graph_token: str = "",
        thread_id: str = "",
        assistant_id: str = "",
        username: str = "",
        timezone: str = "UTC",
        enabled_tools: Optional[list] = None,
        model: str = "",
        instruction: str = "",
        extra_state: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Create a new ADK session with initial state.

        Args:
            app_name: The ADK app/agent name.
            user_id: Unique user identifier.
            auth_token: JWT or bearer token for API auth.
            graph_token: Microsoft Graph API token (for enterprise integrations).
            thread_id: Conversation thread ID.
            assistant_id: ID of the assistant being used.
            username: Display name of the user.
            timezone: User's timezone (e.g., "Europe/Copenhagen").
            enabled_tools: List of enabled tool names.
            model: LLM model identifier.
            instruction: Custom system instruction override.
            extra_state: Additional state key-value pairs.

        Returns:
            The created ADK session object.
        """
        state = {
            SessionKeys.AUTH_TOKEN: auth_token,
            SessionKeys.USER_ID: user_id,
            SessionKeys.USERNAME: username,
            SessionKeys.GRAPH_TOKEN: graph_token,
            SessionKeys.THREAD_ID: thread_id,
            SessionKeys.ASSISTANT_ID: assistant_id,
            SessionKeys.TIMEZONE: timezone,
        }

        if enabled_tools is not None:
            state[SessionKeys.ENABLED_TOOLS] = enabled_tools
        if model:
            state[SessionKeys.MODEL] = model
        if instruction:
            state[SessionKeys.INSTRUCTION] = instruction
        if extra_state:
            state.update(extra_state)

        logger.info(
            "Creating session for app=%s user=%s auth=%s",
            app_name, user_id, _mask_token(auth_token),
        )

        session = await self._session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            state=state,
        )
        return session

    async def update_auth(
        self,
        session: Any,
        auth_token: str = "",
        graph_token: str = "",
    ) -> None:
        """Update authentication tokens in an existing session.

        Args:
            session: The ADK session to update.
            auth_token: New JWT/bearer token.
            graph_token: New Microsoft Graph token.
        """
        if auth_token:
            session.state[SessionKeys.AUTH_TOKEN] = auth_token
        if graph_token:
            session.state[SessionKeys.GRAPH_TOKEN] = graph_token

        logger.debug(
            "Updated session auth: auth=%s graph=%s",
            _mask_token(auth_token), _mask_token(graph_token),
        )

    async def update_config(
        self,
        session: Any,
        *,
        enabled_tools: Optional[list] = None,
        model: str = "",
        instruction: str = "",
        extra_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update agent configuration in an existing session.

        Args:
            session: The ADK session to update.
            enabled_tools: Updated list of enabled tools.
            model: Updated model identifier.
            instruction: Updated system instruction.
            extra_config: Additional config key-value pairs.
        """
        if enabled_tools is not None:
            session.state[SessionKeys.ENABLED_TOOLS] = enabled_tools
        if model:
            session.state[SessionKeys.MODEL] = model
        if instruction:
            session.state[SessionKeys.INSTRUCTION] = instruction
        if extra_config:
            for key, value in extra_config.items():
                session.state[f"config:{key}"] = value

        logger.debug("Updated session config: tools=%s model=%s", enabled_tools, model)
