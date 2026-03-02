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
Telegram channel integration for sunholo.

Provides a BaseChannel implementation for the Telegram Bot API with:
- Webhook parsing and validation
- Message formatting (Markdown → Telegram MarkdownV2)
- Message splitting for Telegram's 4096-char limit
- Media/attachment handling
- Command parsing (/command format)

Usage:
    from sunholo.channels.telegram import TelegramChannel

    channel = TelegramChannel(bot_token="123:ABC...")

    # In a FastAPI webhook handler:
    @app.post("/webhook/telegram")
    async def telegram_webhook(request: Request):
        message = await channel.receive_webhook(request)
        if message:
            response = await process_message(message)
            await channel.send_response(message.channel_id, response)
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import re
from typing import Any, Dict, List, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

from .base import BaseChannel, ChannelMessage, ChannelResponse, ChannelType

logger = logging.getLogger(__name__)

# Telegram message length limit
TELEGRAM_MAX_LENGTH = 4096


def _check_deps():
    if not HTTPX_AVAILABLE:
        raise ImportError(
            "httpx is required for Telegram channel. "
            "Install with: pip install sunholo[channels]"
        )


class TelegramChannel(BaseChannel):
    """Telegram Bot API channel integration.

    Args:
        bot_token: Telegram Bot API token from @BotFather.
        webhook_secret: Secret token for webhook validation (optional).
        parse_mode: Default parse mode ("MarkdownV2", "HTML", "Markdown").
        api_base: Telegram API base URL (for testing/proxies).
    """

    def __init__(
        self,
        bot_token: str,
        webhook_secret: str = "",
        parse_mode: str = "MarkdownV2",
        api_base: str = "https://api.telegram.org",
        config: Dict[str, Any] | None = None,
    ):
        _check_deps()
        super().__init__(channel_type=ChannelType.TELEGRAM, config=config)
        self.bot_token = bot_token
        self.webhook_secret = webhook_secret
        self.parse_mode = parse_mode
        self.api_base = api_base.rstrip("/")
        self._client = httpx.AsyncClient(timeout=30.0)

    @property
    def api_url(self) -> str:
        """Full Telegram Bot API URL."""
        return f"{self.api_base}/bot{self.bot_token}"

    async def receive_webhook(self, request: Any) -> Optional[ChannelMessage]:
        """Parse a Telegram webhook update into a ChannelMessage.

        Args:
            request: FastAPI Request object or dict with update data.

        Returns:
            Parsed ChannelMessage, or None for non-message updates.
        """
        if hasattr(request, "json"):
            update = await request.json()
        elif isinstance(request, dict):
            update = request
        else:
            return None

        # Handle message or edited_message
        message = update.get("message") or update.get("edited_message")
        if not message:
            return None

        chat = message.get("chat", {})
        from_user = message.get("from", {})
        chat_id = str(chat.get("id", ""))
        user_id = str(from_user.get("id", ""))

        # Extract text (could be in text or caption for media messages)
        text = message.get("text", "") or message.get("caption", "")

        # Extract attachments
        attachments = []
        for media_type in ("photo", "document", "audio", "video", "voice", "sticker"):
            media = message.get(media_type)
            if media:
                if media_type == "photo" and isinstance(media, list):
                    # Photos come as an array of sizes, take the largest
                    media = media[-1] if media else None
                if media:
                    attachments.append({
                        "type": media_type,
                        "file_id": media.get("file_id", ""),
                        "file_unique_id": media.get("file_unique_id", ""),
                        "mime_type": media.get("mime_type", ""),
                        "file_name": media.get("file_name", ""),
                        "file_size": media.get("file_size", 0),
                    })

        metadata = {
            "message_id": message.get("message_id"),
            "chat_type": chat.get("type", "private"),
            "username": from_user.get("username", ""),
            "first_name": from_user.get("first_name", ""),
            "last_name": from_user.get("last_name", ""),
        }

        # Check for bot commands
        entities = message.get("entities", [])
        for entity in entities:
            if entity.get("type") == "bot_command":
                metadata["is_command"] = True
                offset = entity["offset"]
                length = entity["length"]
                metadata["command"] = text[offset:offset + length]
                break

        reply_to = ""
        if message.get("reply_to_message"):
            reply_to = str(message["reply_to_message"].get("message_id", ""))

        return ChannelMessage(
            channel_type=ChannelType.TELEGRAM,
            channel_id=chat_id,
            user_id=user_id,
            text=text,
            attachments=attachments,
            metadata=metadata,
            reply_to=reply_to,
            thread_id=chat_id,
        )

    async def send_response(
        self, channel_id: str, response: ChannelResponse
    ) -> bool:
        """Send a response to a Telegram chat.

        Handles message splitting for long responses.

        Args:
            channel_id: Telegram chat_id.
            response: Response to send.

        Returns:
            True if all parts sent successfully.
        """
        text = self.format_message(response.text, response.format)
        chunks = split_message(text, TELEGRAM_MAX_LENGTH)

        success = True
        for chunk in chunks:
            result = await self._send_message(channel_id, chunk)
            if not result:
                success = False

        # Send attachments
        for attachment in response.attachments:
            await self._send_attachment(channel_id, attachment)

        return success

    async def validate_webhook(self, request: Any) -> bool:
        """Validate Telegram webhook using secret token header.

        Args:
            request: FastAPI Request object.

        Returns:
            True if valid (or no secret configured).
        """
        if not self.webhook_secret:
            return True

        if hasattr(request, "headers"):
            token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            return hmac.compare_digest(token, self.webhook_secret)

        return True

    def format_message(self, text: str, format_type: str = "markdown") -> str:
        """Convert text to Telegram MarkdownV2 format.

        Escapes special characters that MarkdownV2 requires.

        Args:
            text: Input text.
            format_type: Input format.

        Returns:
            Telegram-formatted text.
        """
        if self.parse_mode != "MarkdownV2":
            return text

        if format_type == "plain":
            return escape_markdown_v2(text)

        # For markdown input, do selective escaping
        return markdown_to_telegram(text)

    async def _send_message(self, chat_id: str, text: str) -> bool:
        """Send a single message via Telegram API."""
        try:
            resp = await self._client.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": self.parse_mode,
                },
            )
            if resp.status_code != 200:
                data = resp.json()
                logger.error(
                    "Telegram sendMessage failed: %s", data.get("description", resp.status_code)
                )
                # Retry without parse_mode on formatting errors
                if "can't parse" in str(data.get("description", "")).lower():
                    resp = await self._client.post(
                        f"{self.api_url}/sendMessage",
                        json={"chat_id": chat_id, "text": text},
                    )
                    return resp.status_code == 200
                return False
            return True
        except Exception as e:
            logger.error("Failed to send Telegram message: %s", e)
            return False

    async def _send_attachment(self, chat_id: str, attachment: Dict[str, Any]) -> bool:
        """Send a file/media attachment via Telegram API."""
        media_type = attachment.get("type", "document")
        method_map = {
            "photo": "sendPhoto",
            "document": "sendDocument",
            "audio": "sendAudio",
            "video": "sendVideo",
            "voice": "sendVoice",
        }
        method = method_map.get(media_type, "sendDocument")

        payload: Dict[str, Any] = {"chat_id": chat_id}
        if "file_id" in attachment:
            payload[media_type] = attachment["file_id"]
        elif "url" in attachment:
            payload[media_type] = attachment["url"]

        try:
            resp = await self._client.post(
                f"{self.api_url}/{method}", json=payload
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error("Failed to send Telegram attachment: %s", e)
            return False

    async def get_file_url(self, file_id: str) -> Optional[str]:
        """Get a download URL for a Telegram file.

        Args:
            file_id: Telegram file_id from a message attachment.

        Returns:
            Direct download URL, or None on failure.
        """
        try:
            resp = await self._client.get(
                f"{self.api_url}/getFile",
                params={"file_id": file_id},
            )
            if resp.status_code == 200:
                file_path = resp.json().get("result", {}).get("file_path")
                if file_path:
                    return f"{self.api_base}/file/bot{self.bot_token}/{file_path}"
        except Exception as e:
            logger.error("Failed to get file URL: %s", e)
        return None

    async def set_webhook(self, url: str) -> bool:
        """Set the webhook URL for this bot.

        Args:
            url: Public HTTPS URL for webhook.

        Returns:
            True if successfully set.
        """
        payload: Dict[str, Any] = {"url": url}
        if self.webhook_secret:
            payload["secret_token"] = self.webhook_secret

        try:
            resp = await self._client.post(
                f"{self.api_url}/setWebhook", json=payload
            )
            result = resp.json()
            if result.get("ok"):
                logger.info("Telegram webhook set to: %s", url)
                return True
            logger.error("Failed to set webhook: %s", result.get("description"))
        except Exception as e:
            logger.error("Failed to set webhook: %s", e)
        return False

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


def split_message(text: str, max_length: int = TELEGRAM_MAX_LENGTH) -> List[str]:
    """Split a long message into chunks respecting Telegram's limits.

    Tries to split at paragraph boundaries, then sentence boundaries,
    then word boundaries.

    Args:
        text: Text to split.
        max_length: Maximum length per chunk.

    Returns:
        List of text chunks.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Try to find a good break point
        break_at = max_length
        for separator in ["\n\n", "\n", ". ", " "]:
            pos = remaining.rfind(separator, 0, max_length)
            if pos > max_length // 2:
                break_at = pos + len(separator)
                break

        chunks.append(remaining[:break_at].rstrip())
        remaining = remaining[break_at:].lstrip()

    return chunks


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2.

    Args:
        text: Plain text to escape.

    Returns:
        Escaped text safe for MarkdownV2.
    """
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(special_chars)}])", r"\\\1", text)


def markdown_to_telegram(text: str) -> str:
    """Convert standard markdown to Telegram MarkdownV2.

    Handles common patterns while preserving formatting intent.
    This is a best-effort conversion, not a full markdown parser.

    Args:
        text: Standard markdown text.

    Returns:
        Telegram MarkdownV2 formatted text.
    """
    # Escape characters that need escaping outside of formatting
    # But preserve markdown formatting markers
    lines = text.split("\n")
    result = []

    for line in lines:
        # Skip empty lines
        if not line.strip():
            result.append("")
            continue

        # Preserve code blocks
        if line.strip().startswith("```"):
            result.append(line)
            continue

        # Escape special chars that aren't part of formatting
        # This is intentionally conservative
        for char in ".!-()>=#|{}+":
            line = line.replace(char, f"\\{char}")

        result.append(line)

    return "\n".join(result)


def parse_command(text: str) -> tuple[str, str]:
    """Parse a Telegram bot command from message text.

    Args:
        text: Message text (e.g. "/start hello world").

    Returns:
        Tuple of (command, arguments). Command includes the leading /.
        If not a command, returns ("", text).
    """
    if not text or not text.startswith("/"):
        return ("", text)

    parts = text.split(None, 1)
    command = parts[0].split("@")[0]  # Remove @botname suffix
    args = parts[1] if len(parts) > 1 else ""
    return (command, args)
