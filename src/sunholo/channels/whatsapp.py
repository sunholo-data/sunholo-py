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
WhatsApp channel integration via Twilio.

Provides a BaseChannel implementation for WhatsApp messaging with:
- Twilio webhook parsing and validation (HMAC-SHA1)
- Message splitting for WhatsApp's 1600-char limit
- Media/attachment handling via Twilio MediaUrl
- Session management helpers

Usage:
    from sunholo.channels.whatsapp import WhatsAppChannel

    channel = WhatsAppChannel(
        account_sid="AC...",
        auth_token="...",
        from_number="whatsapp:+14155238886",
    )

    # In a FastAPI webhook handler:
    @app.post("/webhook/whatsapp")
    async def whatsapp_webhook(request: Request):
        if not await channel.validate_webhook(request):
            raise HTTPException(403, "Invalid signature")
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
from urllib.parse import urlencode

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TwilioClient = None
    TWILIO_AVAILABLE = False

from .base import BaseChannel, ChannelMessage, ChannelResponse, ChannelType

logger = logging.getLogger(__name__)

# WhatsApp message length limit
WHATSAPP_MAX_LENGTH = 1600


class WhatsAppChannel(BaseChannel):
    """WhatsApp channel integration via Twilio.

    Args:
        account_sid: Twilio Account SID.
        auth_token: Twilio Auth Token (used for webhook validation and API calls).
        from_number: Twilio WhatsApp number (e.g. "whatsapp:+14155238886").
        webhook_url: Your webhook URL (for signature validation).
    """

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        webhook_url: str = "",
        config: Dict[str, Any] | None = None,
    ):
        super().__init__(channel_type=ChannelType.WHATSAPP, config=config)
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.webhook_url = webhook_url
        self._client: Optional[TwilioClient] = None

    @property
    def twilio_client(self) -> TwilioClient:
        """Get or create the Twilio client."""
        if not TWILIO_AVAILABLE:
            raise ImportError(
                "twilio is required for WhatsApp channel. "
                "Install with: pip install sunholo[channels]"
            )
        if self._client is None:
            self._client = TwilioClient(self.account_sid, self.auth_token)
        return self._client

    async def receive_webhook(self, request: Any) -> Optional[ChannelMessage]:
        """Parse a Twilio WhatsApp webhook into a ChannelMessage.

        Args:
            request: FastAPI Request object or dict with form data.

        Returns:
            Parsed ChannelMessage, or None for status callbacks.
        """
        if hasattr(request, "form"):
            form = await request.form()
            data = dict(form)
        elif isinstance(request, dict):
            data = request
        else:
            return None

        # Skip status callback webhooks
        message_sid = data.get("MessageSid") or data.get("SmsSid")
        if not message_sid:
            return None

        from_number = data.get("From", "")
        to_number = data.get("To", "")
        body = data.get("Body", "")
        num_media = int(data.get("NumMedia", "0"))

        # Extract attachments
        attachments = []
        for i in range(num_media):
            media_url = data.get(f"MediaUrl{i}", "")
            media_type = data.get(f"MediaContentType{i}", "")
            if media_url:
                attachments.append({
                    "type": _media_category(media_type),
                    "url": media_url,
                    "mime_type": media_type,
                })

        # Clean phone number for user_id
        user_phone = from_number.replace("whatsapp:", "")

        metadata = {
            "message_sid": message_sid,
            "from_number": from_number,
            "to_number": to_number,
            "profile_name": data.get("ProfileName", ""),
            "num_segments": data.get("NumSegments", "1"),
        }

        return ChannelMessage(
            channel_type=ChannelType.WHATSAPP,
            channel_id=from_number,
            user_id=user_phone,
            text=body,
            attachments=attachments,
            metadata=metadata,
            thread_id=f"whatsapp:{user_phone}",
        )

    async def send_response(
        self, channel_id: str, response: ChannelResponse
    ) -> bool:
        """Send a response via WhatsApp (Twilio).

        Handles message splitting for WhatsApp's length limit.

        Args:
            channel_id: WhatsApp number (e.g. "whatsapp:+1234567890").
            response: Response to send.

        Returns:
            True if all parts sent successfully.
        """
        text = self.format_message(response.text, response.format)
        chunks = split_message(text, WHATSAPP_MAX_LENGTH)

        success = True
        for chunk in chunks:
            result = await self._send_message(channel_id, chunk)
            if not result:
                success = False

        # Send media attachments
        for attachment in response.attachments:
            media_url = attachment.get("url", "")
            if media_url:
                result = await self._send_message(
                    channel_id, attachment.get("caption", ""), media_url=media_url
                )
                if not result:
                    success = False

        return success

    async def validate_webhook(self, request: Any) -> bool:
        """Validate Twilio webhook signature (HMAC-SHA1).

        Args:
            request: FastAPI Request object.

        Returns:
            True if signature is valid.
        """
        if not self.webhook_url:
            return True

        if not hasattr(request, "headers"):
            return True

        signature = request.headers.get("X-Twilio-Signature", "")
        if not signature:
            logger.warning("Missing X-Twilio-Signature header")
            return False

        # Build validation string
        if hasattr(request, "form"):
            form = await request.form()
            params = dict(form)
        else:
            params = {}

        expected = _compute_twilio_signature(
            self.auth_token, self.webhook_url, params
        )
        return hmac.compare_digest(signature, expected)

    def format_message(self, text: str, format_type: str = "markdown") -> str:
        """Convert text to WhatsApp-compatible format.

        WhatsApp supports basic formatting:
        *bold*, _italic_, ~strikethrough~, ```monospace```

        Args:
            text: Input text.
            format_type: Input format.

        Returns:
            WhatsApp-formatted text.
        """
        if format_type == "html":
            return strip_html(text)
        return text

    async def _send_message(
        self,
        to: str,
        body: str,
        media_url: str = "",
    ) -> bool:
        """Send a single message via Twilio."""
        try:
            kwargs: Dict[str, Any] = {
                "from_": self.from_number,
                "to": to,
                "body": body,
            }
            if media_url:
                kwargs["media_url"] = [media_url]

            self.twilio_client.messages.create(**kwargs)
            return True
        except Exception as e:
            logger.error("Failed to send WhatsApp message: %s", e)
            return False


def split_message(text: str, max_length: int = WHATSAPP_MAX_LENGTH) -> List[str]:
    """Split a message into chunks for WhatsApp's character limit.

    Tries to split at paragraph, sentence, then word boundaries.

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

        break_at = max_length
        for separator in ["\n\n", "\n", ". ", " "]:
            pos = remaining.rfind(separator, 0, max_length)
            if pos > max_length // 3:
                break_at = pos + len(separator)
                break

        chunks.append(remaining[:break_at].rstrip())
        remaining = remaining[break_at:].lstrip()

    return chunks


def strip_html(text: str) -> str:
    """Strip HTML tags from text, keeping content."""
    return re.sub(r"<[^>]+>", "", text)


def _media_category(mime_type: str) -> str:
    """Map MIME type to a media category."""
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("video/"):
        return "video"
    if mime_type.startswith("audio/"):
        return "audio"
    return "document"


def _compute_twilio_signature(
    auth_token: str, url: str, params: Dict[str, str]
) -> str:
    """Compute expected Twilio request signature.

    Args:
        auth_token: Twilio auth token.
        url: The full webhook URL.
        params: POST parameters.

    Returns:
        Base64-encoded HMAC-SHA1 signature.
    """
    import base64

    # Sort parameters and append to URL
    sorted_params = sorted(params.items())
    data_str = url + "".join(f"{k}{v}" for k, v in sorted_params)

    # HMAC-SHA1
    mac = hmac.new(
        auth_token.encode("utf-8"),
        data_str.encode("utf-8"),
        hashlib.sha1,
    )
    return base64.b64encode(mac.digest()).decode("utf-8")
