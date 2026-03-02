---
title: Email Channel
sidebar_label: Email
sidebar_position: 4
---

# Email Channel

The `sunholo.channels.email` module provides email integration via SendGrid's Inbound Parse (receiving) and Mail Send API (sending), with Markdown-to-HTML rendering and thread tracking.

## Setup

```python
from sunholo.channels.email import EmailChannel

channel = EmailChannel(
    sendgrid_api_key="SG.xxxxx",       # SendGrid API key
    from_email="bot@yourdomain.com",   # Sender address
    webhook_secret="your-secret",       # Optional: HMAC-SHA256 validation
)
```

## Receiving Emails

Via SendGrid Inbound Parse webhook:

```python
@app.post("/webhook/email")
async def email_webhook(request: Request):
    if not await channel.validate_webhook(request):
        return {"ok": False}

    message = await channel.receive_webhook(request)
    if not message:
        return {"ok": True}

    print(message.text)          # Email body (plain text, HTML stripped)
    print(message.subject)       # Email subject
    print(message.channel_id)    # Sender email address
    print(message.user_id)       # Sender email address
    print(message.thread_id)     # Extracted from email headers
    print(message.reply_to)      # From In-Reply-To header

    # Attachments
    for attachment in message.attachments:
        print(attachment["filename"])
        print(attachment["content_type"])
```

## Sending Responses

Markdown is automatically converted to HTML with professional email styling:

```python
from sunholo.channels.base import ChannelResponse

response = ChannelResponse(
    text="# Summary\n\nHere are the **results**:\n\n- Item 1\n- Item 2",
    format="markdown",
    metadata={"subject": "Re: Your Query"},
)
await channel.send_response("user@example.com", response)
```

The email will include:
- Responsive HTML wrapper with professional styling
- Markdown rendered to HTML (tables, code blocks, lists)
- Proper email headers for threading

## Thread Tracking

Email threads are tracked via standard email headers:

```python
# Thread ID is extracted from:
# 1. References header
# 2. In-Reply-To header
# 3. Message-ID header

message.thread_id  # Extracted thread identifier
message.reply_to   # Message being replied to
```

## Utility Functions

### strip_html_tags

```python
from sunholo.channels.email import strip_html_tags

plain = strip_html_tags("<b>bold</b> text")  # "bold text"
plain = strip_html_tags("<br/>newline")       # Converts <br> to newline
plain = strip_html_tags("&amp; &lt;")         # "& <"
```

### wrap_email_html

```python
from sunholo.channels.email import wrap_email_html

html = wrap_email_html("<p>Hello</p>")
# Returns full HTML document with responsive styling
```

## Webhook Validation

HMAC-SHA256 validation for SendGrid Inbound Parse:

```python
# When webhook_secret is configured, incoming webhooks are validated
# against the X-Webhook-Signature header
```

## Dependencies

- `markdown>=3.5.0` - Markdown to HTML conversion (with tables, fenced_code, nl2br extensions)
- `httpx>=0.25.0` - HTTP client for SendGrid API
