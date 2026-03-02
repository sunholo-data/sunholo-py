---
title: Event Transformer
sidebar_label: Events
sidebar_position: 4
---

# Event Transformer

The `sunholo.adk.events` module transforms ADK execution events into SSE-compatible tool feedback events, enabling real-time UI updates during agent execution.

## ToolFeedback

Represents a tool execution status update:

```python
from sunholo.adk.events import ToolFeedback, FeedbackType

# Tool starting
start = ToolFeedback(
    tool_name="web_search",
    feedback_type=FeedbackType.START,
    message="Searching for 'sunholo documentation'...",
)

# Tool completed
complete = ToolFeedback(
    tool_name="web_search",
    feedback_type=FeedbackType.COMPLETE,
    message="Found 5 results",
    metadata={"result_count": 5},
)

# Tool errored
error = ToolFeedback(
    tool_name="web_search",
    feedback_type=FeedbackType.ERROR,
    message="Search API timeout",
)

# Convert to dict for SSE
data = start.to_dict()
# {"tool_name": "web_search", "type": "start", "message": "Searching...", ...}
```

## FeedbackType Enum

| Value | Description |
|-------|-------------|
| `FeedbackType.START` | Tool execution started |
| `FeedbackType.COMPLETE` | Tool execution completed successfully |
| `FeedbackType.ERROR` | Tool execution failed |

## EventTransformer

Transforms events and manages tool display configuration:

```python
from sunholo.adk.events import EventTransformer

transformer = EventTransformer()

# Register human-readable tool display names
transformer.register_tool_display("web_search", display_name="Web Search")
transformer.register_tool_display("email_send", display_name="Send Email")

# Transform to SSE event
sse_data = transformer.to_sse_event(feedback_event)

# Get tool marker for streaming UI
marker = feedback_event.to_marker()
```
