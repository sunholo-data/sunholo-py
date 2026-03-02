---
title: LiteLLM Compatibility
sidebar_label: LiteLLM Compat
sidebar_position: 7
---

# LiteLLM Compatibility

The `sunholo.adk.litellm_compat` module provides fixes and compatibility layers for using LiteLLM with ADK, particularly for Azure OpenAI and other providers that have edge cases.

## FixedLiteLlm

Extends ADK's `LiteLlm` class with production-discovered fixes:

```python
from sunholo.adk.litellm_compat import FixedLiteLlm

# Use instead of LiteLlm for Azure OpenAI
model = FixedLiteLlm(model="azure/gpt-4o")
```

### Fixes Applied

1. **Null `tool_call.id` fix**: Azure OpenAI sometimes returns null `tool_call.id` values, which ADK rejects. `FixedLiteLlm` auto-generates UUIDs for missing IDs.

2. **Text artifact conversion**: When a model returns text as `inline_data` (binary) instead of text parts, the fix converts them to proper text content.

## Standalone Utilities

These functions can be used independently of ADK:

```python
from sunholo.adk.litellm_compat import (
    generate_tool_call_id,
    is_text_mime_type,
    fix_null_tool_call_ids,
    convert_text_artifacts,
    extract_pdf_text,
)

# Generate a unique tool call ID
tool_id = generate_tool_call_id()  # "call_a1b2c3d4..."

# Check if a MIME type is text-based
is_text_mime_type("text/plain")          # True
is_text_mime_type("application/json")     # True
is_text_mime_type("image/png")           # False

# Fix null tool call IDs in message history
fixed_messages = fix_null_tool_call_ids(messages)

# Convert text inline_data to text parts
fixed_content = convert_text_artifacts(content_parts)
```
