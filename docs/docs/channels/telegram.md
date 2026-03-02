---
title: Telegram Channel
sidebar_label: Telegram
sidebar_position: 2
---

# Telegram Channel

The `sunholo.channels.telegram` module provides a Telegram Bot API integration with message formatting, splitting, and media handling.

## Setup

```python
from sunholo.channels.telegram import TelegramChannel

channel = TelegramChannel(
    bot_token="123456:ABC-DEF...",    # From @BotFather
    webhook_secret="your-secret",      # Optional: webhook validation
    parse_mode="MarkdownV2",           # Default parse mode
)
```

## Receiving Messages

```python
# In a FastAPI webhook handler
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    # Validate webhook (optional)
    if not await channel.validate_webhook(request):
        return {"ok": False}

    # Parse the update
    message = await channel.receive_webhook(request)
    if not message:
        return {"ok": True}  # Non-message update (e.g., callback query)

    # Access message data
    print(message.text)                    # Message text
    print(message.user_id)                 # Telegram user ID
    print(message.channel_id)              # Chat ID
    print(message.metadata["username"])    # Telegram username
    print(message.metadata.get("is_command"))  # True if bot command

    # Handle attachments
    for attachment in message.attachments:
        file_url = await channel.get_file_url(attachment["file_id"])
```

## Sending Responses

Messages are automatically split at paragraph/sentence/word boundaries to respect Telegram's 4,096-character limit:

```python
from sunholo.channels.base import ChannelResponse

response = ChannelResponse(
    text="Your long response here...",
    format="markdown",
    attachments=[{"type": "photo", "file_id": "AgAC..."}],
)
await channel.send_response(message.channel_id, response)
```

## Message Formatting

MarkdownV2 escaping is handled automatically:

```python
# Plain text gets fully escaped
channel.format_message("Hello! How are you?", "plain")
# "Hello\\! How are you\\?"

# Markdown gets selective escaping (preserving formatting)
channel.format_message("**bold** and `code`", "markdown")
```

## Utility Functions

### split_message

Split long text respecting Telegram's limits:

```python
from sunholo.channels.telegram import split_message

chunks = split_message("Very long text...", max_length=4096)
# Splits at: paragraph (\n\n) > newline (\n) > sentence (. ) > word ( )
```

### escape_markdown_v2

Escape special characters for MarkdownV2:

```python
from sunholo.channels.telegram import escape_markdown_v2

safe = escape_markdown_v2("Hello.World!")  # "Hello\\.World\\!"
```

### parse_command

Parse bot commands:

```python
from sunholo.channels.telegram import parse_command

cmd, args = parse_command("/start hello world")
# cmd="/start", args="hello world"

cmd, args = parse_command("/help@mybot")
# cmd="/help", args=""

cmd, args = parse_command("not a command")
# cmd="", args="not a command"
```

## Webhook Setup

```python
# Set the webhook URL for your bot
await channel.set_webhook("https://your-domain.com/webhook/telegram")

# Clean up
await channel.close()
```
