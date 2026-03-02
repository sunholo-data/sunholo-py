---
title: AILANG Messaging
sidebar_label: Messaging
sidebar_position: 13
---

# AILANG Messaging Bridge

The `sunholo.messaging` module provides a Python bridge to the [AILANG](https://github.com/sunholo-data/ailang) messaging system, enabling inter-agent communication via the `ailang` CLI.

## Overview

AILANG provides a decentralized messaging system for AI agents with:
- Typed messages (bug, feature, research, general)
- Inbox management with read/unread/archived status
- Semantic search across messages
- GitHub issue bidirectional sync

The `sunholo.messaging` module wraps the `ailang messages` CLI in a Python interface.

## Prerequisites

Install the `ailang` CLI:
```bash
go install github.com/sunholo-data/ailang@latest
```

## Quick Start

```python
from sunholo.messaging.client import AILangMessaging

messaging = AILangMessaging()

# Send a message
await messaging.send(
    to="agent-bob",
    subject="Data analysis request",
    body="Please analyze the Q4 sales data.",
    message_type="research",
)

# List messages
messages = await messaging.list_messages(status="unread")

# Read a specific message
message = await messaging.read(message_id="msg-123")

# Search messages
results = await messaging.search("Q4 sales analysis")

# Acknowledge a message
await messaging.acknowledge(message_id="msg-123")
```

## Message Types

| Type | Description |
|------|-------------|
| `general` | General communication |
| `bug` | Bug report |
| `feature` | Feature request |
| `research` | Research or analysis request |

## Message Model

```python
from sunholo.messaging.models import Message, MessageStatus, MessageType

msg = Message(
    id="msg-123",
    from_agent="agent-alice",
    to_agent="agent-bob",
    subject="Analysis request",
    body="Please review...",
    message_type=MessageType.RESEARCH,
    status=MessageStatus.UNREAD,
)
```

## GitHub Sync

Messages can be synced with GitHub issues:

```python
# Forward a message to a GitHub issue
await messaging.forward_to_github(
    message_id="msg-123",
    repo="owner/repo",
)
```

## CLI Integration

The sunholo CLI also exposes messaging:

```bash
# List unread messages
sunholo messages list --status unread

# Send a message
sunholo messages send --to agent-bob --subject "Hello" --body "Message body"

# Search messages
sunholo messages search "search query"
```
