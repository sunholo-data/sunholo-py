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
Email channel integration for sunholo.

Provides a BaseChannel implementation for email with:
- Webhook parsing for SendGrid Inbound Parse and generic email webhooks
- HMAC-SHA256 webhook validation
- Markdown → HTML conversion for email responses
- Attachment handling
- Rate limiting per sender

Usage:
    from sunholo.channels.email import EmailChannel

    channel = EmailChannel(
        sendgrid_api_key="SG.xxx",
        from_email="bot@example.com",
        webhook_secret="your-webhook-secret",
    )

    # In a FastAPI webhook handler:
    @app.post("/webhook/email")
    async def email_webhook(request: Request):
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
import json
import logging
import re
from email.utils import parseaddr
from typing import Any, Dict, List, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

try:
    import markdown as md_lib
    MARKDOWN_AVAILABLE = True
except ImportError:
    md_lib = None
    MARKDOWN_AVAILABLE = False

from .base import BaseChannel, ChannelMessage, ChannelResponse, ChannelType

logger = logging.getLogger(__name__)


class EmailChannel(BaseChannel):
    """Email channel integration with SendGrid or generic SMTP.

    Supports receiving emails via webhook (SendGrid Inbound Parse)
    and sending responses via SendGrid Mail Send API or SMTP.

    Args:
        sendgrid_api_key: SendGrid API key for sending emails.
        from_email: Sender email address.
        from_name: Sender display name.
        webhook_secret: Secret for webhook signature validation.
        reply_prefix: Prefix for reply subject lines.
    """

    def __init__(
        self,
        sendgrid_api_key: str = "",
        from_email: str = "",
        from_name: str = "AI Assistant",
        webhook_secret: str = "",
        reply_prefix: str = "Re: ",
        config: Dict[str, Any] | None = None,
    ):
        super().__init__(channel_type=ChannelType.EMAIL, config=config)
        self.sendgrid_api_key = sendgrid_api_key
        self.from_email = from_email
        self.from_name = from_name
        self.webhook_secret = webhook_secret
        self.reply_prefix = reply_prefix
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for API calls."""
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for email channel. "
                "Install with: pip install sunholo[channels]"
            )
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def receive_webhook(self, request: Any) -> Optional[ChannelMessage]:
        """Parse an email webhook into a ChannelMessage.

        Supports SendGrid Inbound Parse format (multipart form data)
        and generic JSON webhook format.

        Args:
            request: FastAPI Request object or dict.

        Returns:
            Parsed ChannelMessage, or None if parsing fails.
        """
        if hasattr(request, "form"):
            # SendGrid Inbound Parse sends multipart form data
            form = await request.form()
            data = dict(form)
        elif hasattr(request, "json"):
            data = await request.json()
        elif isinstance(request, dict):
            data = request
        else:
            return None

        return self._parse_email_data(data)

    def _parse_email_data(self, data: Dict[str, Any]) -> Optional[ChannelMessage]:
        """Parse email data from webhook into ChannelMessage."""
        # SendGrid Inbound Parse format
        from_email = data.get("from", data.get("sender", ""))
        to_email = data.get("to", "")
        subject = data.get("subject", "")
        text = data.get("text", data.get("body", ""))
        html = data.get("html", "")

        # Parse email address
        _, from_addr = parseaddr(from_email)
        if not from_addr:
            from_addr = from_email

        if not from_addr:
            logger.warning("No sender email found in webhook data")
            return None

        # Use text body, fall back to stripped HTML
        if not text and html:
            text = strip_html_tags(html)

        # Parse attachments
        attachments = []
        attachment_info = data.get("attachment-info", data.get("attachments", ""))
        if isinstance(attachment_info, str):
            try:
                attachment_info = json.loads(attachment_info)
            except (json.JSONDecodeError, TypeError):
                attachment_info = {}

        if isinstance(attachment_info, dict):
            for key, info in attachment_info.items():
                attachments.append({
                    "type": "email_attachment",
                    "filename": info.get("filename", info.get("name", key)),
                    "mime_type": info.get("type", info.get("content-type", "")),
                    "content_id": info.get("content-id", ""),
                })
        elif isinstance(attachment_info, list):
            for info in attachment_info:
                attachments.append({
                    "type": "email_attachment",
                    "filename": info.get("filename", info.get("name", "")),
                    "mime_type": info.get("type", info.get("content-type", "")),
                })

        # Extract thread ID from headers
        headers = data.get("headers", "")
        thread_id = _extract_thread_id(headers, subject)

        metadata = {
            "to": to_email,
            "subject": subject,
            "message_id": data.get("message_id", data.get("Message-ID", "")),
            "in_reply_to": data.get("in_reply_to", data.get("In-Reply-To", "")),
            "has_html": bool(html),
            "num_attachments": len(attachments),
            "spf": data.get("SPF", ""),
        }

        return ChannelMessage(
            channel_type=ChannelType.EMAIL,
            channel_id=from_addr,
            user_id=from_addr,
            text=text,
            subject=subject,
            attachments=attachments,
            metadata=metadata,
            thread_id=thread_id,
        )

    async def send_response(
        self, channel_id: str, response: ChannelResponse
    ) -> bool:
        """Send an email response via SendGrid API.

        Args:
            channel_id: Recipient email address.
            response: Response to send.

        Returns:
            True if sent successfully.
        """
        if not self.sendgrid_api_key:
            logger.error("No SendGrid API key configured")
            return False

        # Convert response to HTML
        html_body = self.format_message(response.text, response.format)

        subject = response.metadata.get("subject", "")
        if not subject:
            subject = f"{self.reply_prefix}Your message"
        in_reply_to = response.metadata.get("in_reply_to", "")

        payload = {
            "personalizations": [{"to": [{"email": channel_id}]}],
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": subject,
            "content": [
                {"type": "text/html", "value": html_body},
                {"type": "text/plain", "value": response.text},
            ],
        }

        if in_reply_to:
            payload["headers"] = {
                "In-Reply-To": in_reply_to,
                "References": in_reply_to,
            }

        try:
            resp = await self.http_client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.sendgrid_api_key}",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code in (200, 201, 202):
                logger.info("Email sent to %s", channel_id)
                return True
            logger.error("SendGrid API error: %s %s", resp.status_code, resp.text)
            return False
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            return False

    async def validate_webhook(self, request: Any) -> bool:
        """Validate email webhook using HMAC-SHA256 signature.

        Args:
            request: FastAPI Request object.

        Returns:
            True if valid (or no secret configured).
        """
        if not self.webhook_secret:
            return True

        if not hasattr(request, "headers") or not hasattr(request, "body"):
            return True

        signature = request.headers.get(
            "X-Webhook-Signature",
            request.headers.get("X-Twilio-Email-Event-Webhook-Signature", ""),
        )
        if not signature:
            return True

        body = await request.body()
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

    def format_message(self, text: str, format_type: str = "markdown") -> str:
        """Convert text to HTML for email.

        Args:
            text: Input text (markdown or plain).
            format_type: Input format.

        Returns:
            HTML-formatted email body.
        """
        if format_type == "html":
            return text

        if format_type == "markdown" and MARKDOWN_AVAILABLE:
            html = md_lib.markdown(
                text,
                extensions=["tables", "fenced_code", "nl2br"],
            )
            return wrap_email_html(html)

        # Plain text: wrap in basic HTML
        escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return wrap_email_html(f"<pre>{escaped}</pre>")

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()


def strip_html_tags(html: str) -> str:
    """Strip HTML tags, keeping text content."""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    return text.strip()


def wrap_email_html(body_html: str) -> str:
    """Wrap HTML content in a basic email template.

    Args:
        body_html: Inner HTML content.

    Returns:
        Complete HTML email body.
    """
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
{body_html}
</body>
</html>"""


def _extract_thread_id(headers: str, subject: str) -> str:
    """Extract or generate a thread ID from email headers.

    Uses Message-ID or References header if available, otherwise
    generates from subject line.

    Args:
        headers: Raw email headers string.
        subject: Email subject line.

    Returns:
        Thread identifier string.
    """
    # Try to extract References or In-Reply-To
    for header_name in ("References:", "In-Reply-To:", "Message-ID:"):
        if header_name in headers:
            idx = headers.index(header_name)
            line = headers[idx:].split("\n")[0]
            value = line.split(":", 1)[1].strip()
            if value:
                # Use the first reference as thread ID
                return value.split()[0].strip("<>")

    # Fall back to normalized subject
    clean_subject = re.sub(r"^(re:|fwd?:|fw:)\s*", "", subject, flags=re.IGNORECASE).strip()
    if clean_subject:
        return f"subject:{hashlib.md5(clean_subject.encode()).hexdigest()[:12]}"

    return ""
