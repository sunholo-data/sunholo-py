---
id: channels-index
title: Channels
sidebar_label: Channels
sidebar_position: 4
---

# Channels

The `sunholo.channels` module provides a multi-channel messaging framework with a unified interface for receiving messages from and sending responses to different platforms.

Install with:
```bash
pip install sunholo[channels]
```

## Architecture

All channels implement the `BaseChannel` abstract interface:

```
sunholo.channels
├── base.py       # BaseChannel, ChannelMessage, ChannelResponse, ChannelType
├── email.py      # EmailChannel (SendGrid)
├── telegram.py   # TelegramChannel (Bot API)
└── whatsapp.py   # WhatsAppChannel (Twilio)
```

## Quick Start

```python
from sunholo.channels.telegram import TelegramChannel
from sunholo.channels.base import ChannelResponse

# Create a channel
channel = TelegramChannel(bot_token="123:ABC...")

# In your webhook handler:
async def handle_webhook(request):
    # Parse incoming message
    message = await channel.receive_webhook(request)
    if not message:
        return  # Not a message update

    # Process and respond
    answer = await your_ai_agent(message.text)
    response = ChannelResponse(text=answer)
    await channel.send_response(message.channel_id, response)
```

## Supported Channels

| Channel | Class | Webhook Validation | Message Limit |
|---------|-------|-------------------|---------------|
| [Email](./email.md) | `EmailChannel` | HMAC-SHA256 | Unlimited |
| [Telegram](./telegram.md) | `TelegramChannel` | Secret token header | 4,096 chars |
| [WhatsApp](./whatsapp.md) | `WhatsAppChannel` | HMAC-SHA1 (Twilio) | 1,600 chars |

## BaseChannel Interface

Every channel implements these methods:

```python
class BaseChannel(ABC):
    async def receive_webhook(self, request) -> Optional[ChannelMessage]:
        """Parse incoming webhook into a ChannelMessage."""

    async def send_response(self, channel_id: str, response: ChannelResponse) -> bool:
        """Send a response to a channel."""

    async def validate_webhook(self, request) -> bool:
        """Validate webhook authenticity."""

    def format_message(self, text: str, format_type: str = "markdown") -> str:
        """Format text for the channel's requirements."""

    def get_session_id(self, message: ChannelMessage) -> str:
        """Generate a session ID for conversation tracking."""

    def check_rate_limit(self, user_id: str, max_requests: int = 60) -> bool:
        """Check per-user rate limits."""
```

## ChannelMessage

Unified message format from any channel:

```python
from sunholo.channels.base import ChannelMessage, ChannelType

message = ChannelMessage(
    channel_type=ChannelType.TELEGRAM,
    channel_id="456",              # Chat/conversation ID
    user_id="123",                 # Sender ID
    text="Hello bot",              # Message text
    subject="",                    # Email subject (email only)
    attachments=[],                # Files, images, etc.
    metadata={"username": "user"}, # Platform-specific metadata
    reply_to="",                   # Reply to message ID
    thread_id="",                  # Thread/conversation ID
)
```

## ChannelResponse

Unified response format:

```python
from sunholo.channels.base import ChannelResponse

response = ChannelResponse(
    text="Here's your answer...",
    format="markdown",             # "markdown", "html", or "plain"
    attachments=[],                # Files to send
    metadata={},                   # Platform-specific metadata
)
```

## ChannelType Enum

```python
from sunholo.channels.base import ChannelType

ChannelType.EMAIL      # "email"
ChannelType.TELEGRAM   # "telegram"
ChannelType.WHATSAPP   # "whatsapp"
ChannelType.SLACK      # "slack"
ChannelType.DISCORD    # "discord"
ChannelType.WEB        # "web"
ChannelType.API        # "api"
```

## Dependencies

- `httpx>=0.25.0` - HTTP client (Telegram)
- `twilio>=8.0.0` - Twilio SDK (WhatsApp)
- `markdown>=3.5.0` - Markdown to HTML (Email)
- `aiohttp>=3.9.0` - Async HTTP
