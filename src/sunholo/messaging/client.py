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
Python wrapper around the AILANG messaging CLI.

Provides a clean Python API for inter-agent messaging by delegating
to the `ailang messages` CLI commands.

Usage:
    from sunholo.messaging.client import AILangMessaging

    messaging = AILangMessaging()

    # List messages
    messages = await messaging.list_messages(inbox="myproject", unread=True)

    # Send a message
    await messaging.send("myproject", "Bug found in auth module", title="Auth Bug")

    # Search messages
    results = await messaging.search("authentication error", neural=True)
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from .models import Message, MessageStatus

logger = logging.getLogger(__name__)


class AILangNotFoundError(Exception):
    """Raised when the ailang CLI is not found on PATH."""
    pass


class AILangMessaging:
    """Python bridge to the AILANG messaging system.

    Wraps the `ailang messages` CLI to provide Python-native access
    to inter-agent messaging, inbox management, and semantic search.

    Args:
        ailang_path: Path to the ailang binary. Defaults to finding it on PATH.
        timeout: Default timeout in seconds for CLI commands.
    """

    def __init__(self, ailang_path: str = "", timeout: int = 30):
        if ailang_path:
            self._ailang = ailang_path
        else:
            found = shutil.which("ailang")
            if not found:
                raise AILangNotFoundError(
                    "ailang CLI not found on PATH. "
                    "Install from: https://github.com/ailang/ailang"
                )
            self._ailang = found

        self.timeout = timeout

    def _run(self, args: List[str], timeout: int | None = None) -> str:
        """Execute an ailang CLI command and return stdout.

        Args:
            args: Command arguments (after 'ailang').
            timeout: Command timeout in seconds.

        Returns:
            Command stdout as string.

        Raises:
            subprocess.CalledProcessError: If the command fails.
            subprocess.TimeoutExpired: If the command times out.
        """
        cmd = [self._ailang] + args
        logger.debug("Running: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout or self.timeout,
        )

        if result.returncode != 0:
            logger.error("ailang command failed: %s", result.stderr)
            result.check_returncode()

        return result.stdout

    def _run_json(self, args: List[str], timeout: int | None = None) -> Any:
        """Execute an ailang command and parse JSON output.

        Args:
            args: Command arguments (should include --json flag).
            timeout: Command timeout in seconds.

        Returns:
            Parsed JSON output.
        """
        output = self._run(args + ["--json"], timeout=timeout)
        return json.loads(output)

    def list_messages(
        self,
        inbox: str = "",
        unread: bool = False,
        limit: int = 50,
    ) -> List[Message]:
        """List messages, optionally filtered by inbox and status.

        Args:
            inbox: Filter to specific inbox.
            unread: Show only unread messages.
            limit: Maximum number of messages.

        Returns:
            List of Message objects.
        """
        args = ["messages", "list"]
        if inbox:
            args.extend(["--inbox", inbox])
        if unread:
            args.append("--unread")

        try:
            data = self._run_json(args)
            messages = []
            for item in (data if isinstance(data, list) else []):
                messages.append(Message.from_dict(item))
            return messages[:limit]
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to list messages: %s", e)
            return []

    def read_message(self, message_id: str, peek: bool = False) -> Optional[Message]:
        """Read a specific message.

        Args:
            message_id: The message ID.
            peek: If True, don't mark as read.

        Returns:
            Message object or None if not found.
        """
        args = ["messages", "read", message_id]
        if peek:
            args.append("--peek")

        try:
            data = self._run_json(args)
            return Message.from_dict(data)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to read message %s: %s", message_id, e)
            return None

    def send(
        self,
        inbox: str,
        body: str,
        *,
        title: str = "",
        from_agent: str = "",
        github: bool = False,
    ) -> bool:
        """Send a message to an inbox.

        Args:
            inbox: Target inbox name.
            body: Message body text.
            title: Optional message title.
            from_agent: Sender agent name.
            github: Also create a GitHub issue.

        Returns:
            True if sent successfully.
        """
        args = ["messages", "send", inbox, body]
        if title:
            args.extend(["--title", title])
        if from_agent:
            args.extend(["--from", from_agent])
        if github:
            args.append("--github")

        try:
            self._run(args)
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to send message: %s", e)
            return False

    def search(
        self,
        query: str,
        *,
        neural: bool = False,
        space: str = "",
    ) -> List[Message]:
        """Search messages using text or semantic search.

        Args:
            query: Search query string.
            neural: Use neural/semantic search instead of text search.
            space: Search space ("code", "intent", "resolution").

        Returns:
            List of matching Message objects.
        """
        args = ["messages", "search", query]
        if neural:
            args.append("--neural")
        if space:
            args.extend(["--space", space])

        try:
            data = self._run_json(args)
            return [Message.from_dict(item) for item in (data if isinstance(data, list) else [])]
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to search messages: %s", e)
            return []

    def acknowledge(self, message_id: str) -> bool:
        """Mark a message as acknowledged.

        Args:
            message_id: The message ID.

        Returns:
            True if acknowledged successfully.
        """
        try:
            self._run(["messages", "ack", message_id])
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to acknowledge message %s: %s", message_id, e)
            return False

    def forward(self, message_id: str, to_inbox: str) -> bool:
        """Forward a message to another inbox.

        Args:
            message_id: The message ID.
            to_inbox: Destination inbox.

        Returns:
            True if forwarded successfully.
        """
        try:
            self._run(["messages", "forward", "--to", to_inbox, message_id])
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to forward message %s: %s", message_id, e)
            return False

    def is_available(self) -> bool:
        """Check if the ailang CLI is available and working."""
        try:
            self._run(["--version"], timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
