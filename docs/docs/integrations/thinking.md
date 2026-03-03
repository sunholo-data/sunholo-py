---
title: Thinking Capture
sidebar_label: Thinking Capture
sidebar_position: 12
---

# Thinking Capture

The `sunholo.genai.thinking` module extracts and processes "thinking" or "reasoning" content from LLM responses that support extended thinking (e.g., Anthropic Claude with extended thinking, Google Gemini with thinking mode).

## Extract from Complete Responses

### Simple Extraction

```python
from sunholo.genai.thinking import extract_thinking_simple

text = """<thinking>Let me analyze this step by step.
First, the user wants to know about pricing.
I should check the latest pricing page.</thinking>
Based on the current pricing, the plan costs $49/month."""

thinking, response = extract_thinking_simple(text)
# thinking = "Let me analyze this step by step.\nFirst, the user..."
# response = "Based on the current pricing, the plan costs $49/month."
```

### Detailed Extraction

```python
from sunholo.genai.thinking import extract_thinking, ThinkingContent

text = """<thinking>Analysis...</thinking>
Middle text.
<reflection>Let me reconsider...</reflection>
Final answer."""

contents, cleaned = extract_thinking(text)
# contents = [
#   ThinkingContent(text="Analysis...", tag_type="thinking"),
#   ThinkingContent(text="Let me reconsider...", tag_type="reflection"),
# ]
# cleaned = "Middle text.\nFinal answer."
```

### Supported Tags

| Tag | Description |
|-----|-------------|
| `<thinking>...</thinking>` | Standard thinking block |
| `<antThinking>...</antThinking>` | Anthropic thinking format |
| `<reflection>...</reflection>` | Reflection/reconsideration block |

## Streaming Capture

Separate thinking from response content in real-time during streaming:

```python
from sunholo.genai.thinking import ThinkingCapture

capture = ThinkingCapture()

# Process streaming chunks
for chunk in llm_stream:
    response_text = capture.process_chunk(chunk)
    if response_text:
        # Send to UI (thinking content is filtered out)
        send_to_client(response_text)

# Flush remaining content
remaining = capture.flush()
if remaining:
    send_to_client(remaining)

# Access captured thinking
thinking = capture.get_thinking()
response = capture.get_response()
print(f"Model thought: {thinking}")
```

### Custom Tags

```python
# Capture with a custom tag name
capture = ThinkingCapture(tag="reflection")
```

### State Management

```python
capture.is_in_thinking  # True if currently inside a thinking block
capture.reset()         # Reset for reuse
```

## Anthropic Extended Thinking

Handle Anthropic's native thinking block format (separate content blocks, not tags):

```python
from sunholo.genai.thinking import extract_anthropic_thinking

# response is an Anthropic Message object with content blocks
thinking, response_text = extract_anthropic_thinking(response)
# thinking = content from blocks with type="thinking"
# response_text = content from blocks with type="text"
```

## Streaming Callback Factory

Create a callback that routes thinking and response content to separate handlers:

```python
from sunholo.genai.thinking import create_thinking_callback

thinking_chunks = []
response_chunks = []

callback = create_thinking_callback(
    on_thinking=thinking_chunks.append,
    on_response=response_chunks.append,
)

# Use as a streaming callback
for chunk in llm_stream:
    callback(chunk)
```
