---
title: WhatsApp Channel
sidebar_label: WhatsApp
sidebar_position: 3
---

# WhatsApp Channel

The `sunholo.channels.whatsapp` module provides WhatsApp integration via the Twilio API with webhook validation, media handling, and message splitting.

## Setup

```python
from sunholo.channels.whatsapp import WhatsAppChannel

channel = WhatsAppChannel(
    account_sid="ACxxxxxxxxx",           # Twilio Account SID
    auth_token="your_auth_token",        # Twilio Auth Token
    from_number="whatsapp:+14155238886", # Your Twilio WhatsApp number
)
```

## Receiving Messages

```python
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    # Validate Twilio signature
    if not await channel.validate_webhook(request):
        return {"ok": False}

    message = await channel.receive_webhook(request)
    if not message:
        return {"ok": True}  # Status callback, not a message

    print(message.text)          # "Hello from WhatsApp"
    print(message.channel_id)    # "whatsapp:+1234567890"
    print(message.user_id)       # "+1234567890" (without whatsapp: prefix)

    # Handle media attachments
    for attachment in message.attachments:
        print(attachment["type"])      # "image", "audio", "document", etc.
        print(attachment["url"])       # Media URL
        print(attachment["mime_type"]) # "image/jpeg", etc.
```

## Sending Responses

Messages are automatically split to respect WhatsApp's 1,600-character limit:

```python
from sunholo.channels.base import ChannelResponse

response = ChannelResponse(text="Your response here...")
await channel.send_response(message.channel_id, response)
```

## Webhook Validation

Twilio signature validation using HMAC-SHA1:

```python
# Validation requires the full webhook URL and auth token
# The channel handles this automatically when auth_token is provided

valid = await channel.validate_webhook(request)
```

## Utility Functions

### split_message

```python
from sunholo.channels.whatsapp import split_message

chunks = split_message("Long text...", max_length=1600)
```

### strip_html

Remove HTML tags for plain text display:

```python
from sunholo.channels.whatsapp import strip_html

plain = strip_html("<b>bold</b> text")  # "bold text"
```

## Dependencies

- `twilio>=8.0.0` - Twilio Python SDK
- `httpx>=0.25.0` - HTTP client
