---
title: Session Helper
sidebar_label: Session
sidebar_position: 3
---

# Session Helper

The `sunholo.adk.session` module manages ADK session creation with authentication injection, providing a standardized way to pass user context through agent sessions.

## SessionKeys

Standard keys for session state:

```python
from sunholo.adk.session import SessionKeys

SessionKeys.USER_ID       # "user:user_id"
SessionKeys.AUTH_TOKEN    # "user:auth_token"
SessionKeys.CONFIG        # "user:config"
SessionKeys.PREFERENCES   # "user:preferences"
```

## SessionHelper

Build session state with user context for ADK agents:

```python
from sunholo.adk.session import SessionHelper

helper = SessionHelper()

# Build session state with user info
state = helper.build_session_state(
    user_id="user@example.com",
    auth_token="bearer_token_abc123",
    config={"model": "gemini-2.0-flash", "temperature": 0.7},
    extra={"custom_field": "custom_value"},
)

# state = {
#   "user:user_id": "user@example.com",
#   "user:auth_token": "***<masked>",
#   "user:config": {"model": "gemini-2.0-flash", ...},
#   "custom_field": "custom_value",
# }
```

### Token Masking

Auth tokens are automatically masked in session state for logging safety. The `_mask_token()` method hashes tokens using SHA256, storing `***{hash_prefix}` instead of the raw token.
