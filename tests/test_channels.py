"""Tests for sunholo.channels module."""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from sunholo.channels.base import (
    BaseChannel, ChannelMessage, ChannelResponse, ChannelType,
)


# Concrete implementation for testing
class DummyChannel(BaseChannel):
    async def receive_webhook(self, request):
        return ChannelMessage(
            channel_type=self.channel_type,
            channel_id="test-123",
            user_id="user-456",
            text="Hello",
        )

    async def send_response(self, channel_id, response):
        return True

    async def validate_webhook(self, request):
        return True


class TestChannelMessage:
    def test_create_message(self):
        msg = ChannelMessage(
            channel_type=ChannelType.EMAIL,
            channel_id="test@example.com",
            user_id="test@example.com",
            text="Hello world",
            subject="Test subject",
        )
        assert msg.channel_type == ChannelType.EMAIL
        assert msg.text == "Hello world"
        assert msg.subject == "Test subject"
        assert msg.attachments == []
        assert msg.metadata == {}

    def test_message_with_attachments(self):
        msg = ChannelMessage(
            channel_type=ChannelType.TELEGRAM,
            channel_id="123",
            user_id="456",
            text="Check this file",
            attachments=[{"type": "document", "file_id": "abc"}],
        )
        assert len(msg.attachments) == 1
        assert msg.attachments[0]["type"] == "document"

    def test_message_timestamp(self):
        before = time.time()
        msg = ChannelMessage(
            channel_type=ChannelType.WHATSAPP,
            channel_id="+1234567890",
            user_id="+1234567890",
            text="Test",
        )
        after = time.time()
        assert before <= msg.timestamp <= after


class TestChannelResponse:
    def test_create_response(self):
        resp = ChannelResponse(text="Hello back")
        assert resp.text == "Hello back"
        assert resp.format == "markdown"
        assert resp.attachments == []

    def test_response_with_metadata(self):
        resp = ChannelResponse(
            text="Reply",
            metadata={"subject": "Re: Test"},
            format="html",
        )
        assert resp.metadata["subject"] == "Re: Test"
        assert resp.format == "html"


class TestBaseChannel:
    def test_channel_type(self):
        channel = DummyChannel(ChannelType.TELEGRAM)
        assert channel.channel_type == ChannelType.TELEGRAM

    def test_default_format_message(self):
        channel = DummyChannel(ChannelType.TELEGRAM)
        assert channel.format_message("hello") == "hello"

    def test_session_id(self):
        channel = DummyChannel(ChannelType.EMAIL)
        msg = ChannelMessage(
            channel_type=ChannelType.EMAIL,
            channel_id="test@example.com",
            user_id="test@example.com",
            text="Hi",
        )
        session_id = channel.get_session_id(msg)
        assert session_id == "email:test@example.com"

    def test_rate_limit_allows_within_limit(self):
        channel = DummyChannel(ChannelType.TELEGRAM)
        for _ in range(5):
            assert channel.check_rate_limit("user1", max_requests=5)
        # 6th request should be denied
        assert not channel.check_rate_limit("user1", max_requests=5)

    def test_rate_limit_different_users(self):
        channel = DummyChannel(ChannelType.TELEGRAM)
        for _ in range(5):
            channel.check_rate_limit("user1", max_requests=5)
        # Different user should still be allowed
        assert channel.check_rate_limit("user2", max_requests=5)


class TestTelegramChannel:
    def test_split_message_short(self):
        from sunholo.channels.telegram import split_message
        chunks = split_message("Hello world", 4096)
        assert chunks == ["Hello world"]

    def test_split_message_long(self):
        from sunholo.channels.telegram import split_message
        text = "A" * 5000
        chunks = split_message(text, 4096)
        assert len(chunks) == 2
        assert all(len(c) <= 4096 for c in chunks)
        assert "".join(chunks) == text

    def test_split_message_at_paragraph(self):
        from sunholo.channels.telegram import split_message
        text = "A" * 3000 + "\n\n" + "B" * 2000
        chunks = split_message(text, 4096)
        assert len(chunks) == 2
        assert chunks[0].endswith("A" * 10)  # Should split at paragraph
        assert chunks[1].startswith("B")

    def test_escape_markdown_v2(self):
        from sunholo.channels.telegram import escape_markdown_v2
        assert escape_markdown_v2("hello.world") == "hello\\.world"
        assert escape_markdown_v2("test!") == "test\\!"
        assert escape_markdown_v2("a_b") == "a\\_b"

    def test_parse_command(self):
        from sunholo.channels.telegram import parse_command
        cmd, args = parse_command("/start hello world")
        assert cmd == "/start"
        assert args == "hello world"

        cmd, args = parse_command("/help")
        assert cmd == "/help"
        assert args == ""

        cmd, args = parse_command("not a command")
        assert cmd == ""
        assert args == "not a command"

    def test_parse_command_with_botname(self):
        from sunholo.channels.telegram import parse_command
        cmd, args = parse_command("/start@mybot hello")
        assert cmd == "/start"
        assert args == "hello"

    @pytest.mark.asyncio
    async def test_receive_webhook_dict(self):
        from sunholo.channels.telegram import TelegramChannel
        channel = TelegramChannel(bot_token="fake:token")

        update = {
            "message": {
                "message_id": 1,
                "from": {"id": 123, "username": "testuser", "first_name": "Test"},
                "chat": {"id": 456, "type": "private"},
                "text": "Hello bot",
            }
        }

        msg = await channel.receive_webhook(update)
        assert msg is not None
        assert msg.channel_type == ChannelType.TELEGRAM
        assert msg.channel_id == "456"
        assert msg.user_id == "123"
        assert msg.text == "Hello bot"

    @pytest.mark.asyncio
    async def test_receive_webhook_no_message(self):
        from sunholo.channels.telegram import TelegramChannel
        channel = TelegramChannel(bot_token="fake:token")

        update = {"callback_query": {"data": "button_click"}}
        msg = await channel.receive_webhook(update)
        assert msg is None


class TestWhatsAppChannel:
    def test_split_message_short(self):
        from sunholo.channels.whatsapp import split_message
        chunks = split_message("Hello", 1600)
        assert chunks == ["Hello"]

    def test_split_message_long(self):
        from sunholo.channels.whatsapp import split_message
        text = "Word " * 400  # ~2000 chars
        chunks = split_message(text, 1600)
        assert len(chunks) >= 2
        assert all(len(c) <= 1600 for c in chunks)

    def test_strip_html(self):
        from sunholo.channels.whatsapp import strip_html
        assert strip_html("<b>bold</b>") == "bold"
        assert strip_html("<p>paragraph</p>") == "paragraph"

    @pytest.mark.asyncio
    async def test_receive_webhook_dict(self):
        from sunholo.channels.whatsapp import WhatsAppChannel
        channel = WhatsAppChannel(
            account_sid="ACtest",
            auth_token="test_token",
            from_number="whatsapp:+14155238886",
        )

        data = {
            "MessageSid": "SM123",
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "Hello from WhatsApp",
            "NumMedia": "0",
            "ProfileName": "Test User",
        }

        msg = await channel.receive_webhook(data)
        assert msg is not None
        assert msg.channel_type == ChannelType.WHATSAPP
        assert msg.channel_id == "whatsapp:+1234567890"
        assert msg.user_id == "+1234567890"
        assert msg.text == "Hello from WhatsApp"

    @pytest.mark.asyncio
    async def test_receive_webhook_with_media(self):
        from sunholo.channels.whatsapp import WhatsAppChannel
        channel = WhatsAppChannel(
            account_sid="ACtest",
            auth_token="test_token",
            from_number="whatsapp:+14155238886",
        )

        data = {
            "MessageSid": "SM456",
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "Check this photo",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/media/123",
            "MediaContentType0": "image/jpeg",
        }

        msg = await channel.receive_webhook(data)
        assert msg is not None
        assert len(msg.attachments) == 1
        assert msg.attachments[0]["type"] == "image"
        assert msg.attachments[0]["mime_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_receive_webhook_status_callback(self):
        from sunholo.channels.whatsapp import WhatsAppChannel
        channel = WhatsAppChannel(
            account_sid="ACtest",
            auth_token="test_token",
            from_number="whatsapp:+14155238886",
        )

        # Status callback has no MessageSid
        data = {"AccountSid": "ACtest", "MessageStatus": "delivered"}
        msg = await channel.receive_webhook(data)
        assert msg is None


class TestEmailChannel:
    def test_strip_html_tags(self):
        from sunholo.channels.email import strip_html_tags
        assert strip_html_tags("<b>bold</b> text") == "bold text"
        assert "newline" in strip_html_tags("<br/>newline")
        assert strip_html_tags("&amp; &lt; &gt;") == "& < >"

    def test_wrap_email_html(self):
        from sunholo.channels.email import wrap_email_html
        html = wrap_email_html("<p>Hello</p>")
        assert "<p>Hello</p>" in html
        assert "<!DOCTYPE html>" in html
        assert "font-family" in html

    @pytest.mark.asyncio
    async def test_receive_webhook_dict(self):
        from sunholo.channels.email import EmailChannel
        channel = EmailChannel(
            sendgrid_api_key="SG.test",
            from_email="bot@example.com",
        )

        data = {
            "from": "user@example.com",
            "to": "bot@example.com",
            "subject": "Test Email",
            "text": "Hello from email",
        }

        msg = await channel.receive_webhook(data)
        assert msg is not None
        assert msg.channel_type == ChannelType.EMAIL
        assert msg.channel_id == "user@example.com"
        assert msg.text == "Hello from email"
        assert msg.subject == "Test Email"

    @pytest.mark.asyncio
    async def test_receive_webhook_html_fallback(self):
        from sunholo.channels.email import EmailChannel
        channel = EmailChannel()

        data = {
            "from": "user@example.com",
            "to": "bot@example.com",
            "subject": "HTML Email",
            "html": "<p>Hello from <b>HTML</b></p>",
        }

        msg = await channel.receive_webhook(data)
        assert msg is not None
        assert "Hello from" in msg.text
        assert "<b>" not in msg.text  # HTML should be stripped

    @pytest.mark.asyncio
    async def test_validate_webhook_no_secret(self):
        from sunholo.channels.email import EmailChannel
        channel = EmailChannel()
        assert await channel.validate_webhook({})

    @pytest.mark.asyncio
    async def test_receive_webhook_no_sender(self):
        from sunholo.channels.email import EmailChannel
        channel = EmailChannel()
        data = {"to": "bot@example.com", "text": "No sender"}
        msg = await channel.receive_webhook(data)
        assert msg is None
